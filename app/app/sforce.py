from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.utils import timezone

import logging
import salesforce

_logger = logging.getLogger('movements-alerts')

from app.market.models import MarketItem, MarketItemSalesforceRecord


def _dict_for_salesforce(market_item):
    countries = market_item.countries.all()
    region_dict = {}
    for c in countries:
        if c.region_id not in region_dict:
            region_dict[c.region_id] = c.region.name
    regions = region_dict.values()
    if len(regions) >= 3:
        regions.append('Global')
    return {
        'Movements_Number__c': market_item.id,
        'Movements_Title__c': market_item.title,
        'Movements_URL__c': settings.BASE_URL + reverse('show_post', args=[market_item.id]),
        'Request_Offer__c': market_item.item_type,
        'Request_Summary__c': market_item.details[:200],
        'Resolution_Type__c': market_item.get_status_display(),
        'Screen_Name__c': market_item.owner.username,
        'Manager__c': market_item.staff_owner.username if market_item.staff_owner else '',
        'Case_Comment__c': market_item.commentcount,
        'Case_Emails__c': market_item.email_rec_count,
        'Case_Messages__c': market_item.total_msg_count,
        'Case_Views__c': market_item.total_view_count,
        'Date_Posted__c': market_item.pub_date.date().isoformat(),
        'Published__c': market_item.published,
        'Skill__c': ';'.join([market_item.specific_skill or ''] + [i.name for i in market_item.interests.all()]),
        'Issues__c': ';'.join([market_item.specific_issue or ''] + [i.issues for i in market_item.issues.all()]),
        'Location__c': ';'.join([x.countries for x in countries]),
        'Region__c': ';'.join(regions),
    }


def _authenticate():
    if not settings.SALESFORCE_INTEGRATION_ENABLED:
        return None
    sfdc = salesforce.Salesforce(sandbox=settings.SALESFORCE_USE_SANDBOX, version=31.0)
    sfdc.authenticate(username=settings.SALESFORCE_USERNAME,
                      password=settings.SALESFORCE_PASSWORD,
                      client_id=settings.SALESFORCE_CLIENT_ID,
                      client_secret=settings.SALESFORCE_CLIENT_SECRET)
    return sfdc


def _get_market_item(item_id):
    item = MarketItem \
        .objects \
        .select_for_update() \
        .select_related('owner') \
        .prefetch_related('issues', 'countries') \
        .get(pk=item_id)
    counts = MarketItem.objects.annotate(email_rec_count=Count('emailrecommendation', distinct=True),
                                         total_msg_count=Count('messageext', distinct=True),
                                         total_view_count=Count('marketitemviewcounter', distinct=True),)\
        .get(pk=item_id)
    item.email_rec_count = counts.email_rec_count
    item.total_msg_count = counts.total_msg_count
    item.total_view_count = counts.total_view_count
    return item


def _update_case(sfdc, market_item, record_id):
    try:
        sfdc.Case.update([record_id, _dict_for_salesforce(market_item)])
    except ValueError:
        # The salesforce API returns a value error on success as it tries to parse the response as JSON and it isn't
        pass
    MarketItemSalesforceRecord.objects \
        .filter(item=market_item) \
        .update(needs_updating=False, last_updated=timezone.now())


def _create_case(sfdc, market_item):
    result = sfdc.Case.create(_dict_for_salesforce(market_item))
    item = MarketItemSalesforceRecord(item=market_item,
                                      salesforce_record_id=result['id'],
                                      last_updated=timezone.now(),
                                      needs_updating=False)
    item.save()


def _find_and_update_case(sfdc, market_item):
    result = sfdc.query("SELECT ID FROM Case WHERE Movements_Number__c={0}".format(market_item.id))
    if not result['totalSize']:
        return False
    record_id = result['records'][0]['Id']
    _update_case(sfdc, market_item, record_id)
    item = MarketItemSalesforceRecord(item=market_item,
                                      salesforce_record_id=record_id,
                                      last_updated=timezone.now(),
                                      needs_updating=False)
    item.save()
    return True


def add_market_item_to_salesforce(market_item):
    try:
        with transaction.atomic():
            market_item = _get_market_item(market_item.id)
            sfdc = _authenticate()
            if sfdc is None:
                return
            try:
                if market_item.salesforce:
                    _update_case(sfdc, market_item, market_item.salesforce.salesforce_record_id)
            except ObjectDoesNotExist:
                if not _find_and_update_case(sfdc, market_item):
                    _create_case(sfdc, market_item)
    except Exception as ex:
        _logger.exception(ex)


def update_market_item_stats():
    for record in MarketItemSalesforceRecord.objects.filter(needs_updating=True):
        _logger.info('Updating stats in salesforce for market item {0}'.format(record.item.id))
        add_market_item_to_salesforce(record.item)


def run_backport():
    items = MarketItem.objects.filter(salesforce=None)
    for market_item in items:
        add_market_item_to_salesforce(market_item)
