window.ahr = window.ahr || {};
window.ahr.market = window.ahr.market || {};

window.ahr.market.MarketBaseView = window.ahr.BaseView.extend({
    el: '#market',
    loadingScrollElemets: false,
    itemCount: 0,
    currentItem: 0,
    allItemsLoaded: false,
    itemsPerCall: 15,
    requiresResetOnNewOfferRequest: false,


    create_request: function(){
        this.requestdialog.showModal(true);
        if(this.requiresResetOnNewOfferRequest && !this.requestdialog.oncomplete){
            var self = this;
            this.requestdialog.oncomplete = function(){
                self.resetMarket();
            };
        }
    },
    create_offer: function(){
        this.offerdialog.showModal(true);
        if(this.requiresResetOnNewOfferRequest && !this.offerdialog.oncomplete){
            var self = this;
            this.offerdialog.oncomplete = function(){
                self.resetMarket();
            };
        }
    },

    setFilterNone:function(){
        $('.item-type').addClass('btn-success');
        this.filters = window.ahr.clone(this.default_filters);
        var skillarr=[];
        _.each(window.ahr.skills, function(item){
            skillarr.push(parseInt(item.pk, 10));
        });
        this.filters.skills =  skillarr;

        var countriesarr=[];
        _.each(window.ahr.countries, function(item){
            countriesarr.push(parseInt(item.pk, 10));
        });
        this.filters.countries =  countriesarr;

        var isssuesarr=[];
        _.each(window.ahr.issues, function(item){
            isssuesarr.push(parseInt(item.pk, 10));
        });
        this.filters.issues =  isssuesarr;
    },

    setFilterKeys:function(){
        var that = this;
        for(var key in this.filters){
            $('.row.'+key).empty();
            this.initFilters(that, key, that.tagtemp);
        }
    },

    changeFilterType: function(ev){
        var that = this;
        $('.filter-type').removeClass('btn-success');

        $(ev.currentTarget).addClass('btn-success');
        if(ev.currentTarget.textContent=="Default"){
            this.filters = window.ahr.clone(this.default_filters);
            $('.item-type').addClass('btn-success');
        }else if(ev.currentTarget.textContent=="All"){
            this.setFilterNone();
        }
        this.setFilterKeys();
        this.resetMarket();
    },

    showItem: function(ev){
        var that = this;
        var id = ev.currentTarget.getAttribute('item_id');
        this.marketitemdialog.show(id,that);
    },

    getItems: function(from,to,filters,aurl){
        filters.search=$('#q').val();
        return $.ajax({
            url: aurl.replace('0',from)+to,
            dataType: 'json',
            contentType:"application/json; charset=utf-8",
            data: filters,
            traditional: true
        });
    },

    getItemsCount: function(filters,aurl){
        return $.ajax({
            url: aurl,
            dataType: 'json',
            contentType:"application/json; charset=utf-8",
            data: filters,
            traditional: true
        });
    },

    levelReached: function(){
      // is it low enough to add elements to bottom?
      var pageHeight = Math.max(document.body.scrollHeight ||
        document.body.offsetHeight);
      var viewportHeight = window.innerHeight  ||
        document.documentElement.clientHeight  ||
        document.body.clientHeight || 0;
      var scrollHeight = window.pageYOffset ||
        document.documentElement.scrollTop  ||
        document.body.scrollTop || 0;
      // Trigger for scrolls within 30 pixels from page bottom
      return pageHeight - viewportHeight - scrollHeight < 30;
    },

    initInfiniteScroll: function(){
        $('#marketitems').empty();
        this.allItemsLoaded = false;
        this.currentItem = 0;
        this.itemCount = this.getItemsCount(this.filters, this.itemcount_url);

        var $container = $('#marketitems');
        $container.masonry({
            itemSelector: '.market-place-item'
        });

        this.loadScrollElements(this);
        var that = this;
        $(window).scroll(function() {
            that.loadScrollElements(that);
        });
    },

    loadScrollElements: function(self){
        var that = self;
        if(!that.loadingScrollElemets && that.levelReached() && !that.allItemsLoaded) {
            that.loadingScrollElemets = true;
            var dfrd = that.getItems(
                                    that.currentItem,
                                    that.currentItem + that.itemsPerCall,
                                    that.filters,
                                    that.getitemfromto
                                );

            var itemsToAppend = [];
            dfrd.done(function(data){
                if(data.length === 0){
                    that.allItemsLoaded = true;
                }
                _.each(data, function(item){
                    item.fields.pk = item.pk;
                    var item_html = that.item_tmp(item.fields);
                    itemsToAppend.push(item_html);
                    $('#marketitems').append(item_html);
                });

                if(itemsToAppend.length > 0){
                    var container = document.querySelector('#marketitems');
                    that.msnry = new Masonry( container );
                    _.each(itemsToAppend, function(elem){
                        that.msnry.appended( elem );
                    });
                    that.msnry.layout();
                }
                that.afterset();
                that.currentItem = that.currentItem + that.itemsPerCall;
                that.loadingScrollElemets = false;
            });
        }
    },

    refreshScrollElements: function(){
        // var container = document.querySelector('#marketitems');
        // var msnry = new Masonry( container );
        this.msnry.layout();
    },

    afterset: function(){
        $('.numstars').rateit();
        $('.numstars').rateit('min',0);
        $('.numstars').rateit('max',5);
        $('.numstars').rateit('readonly',true);
        $('.numstars').each(function(){
            $(this).rateit('value',this.getAttribute('score'));
        });
    },

    resetMarket: function(){
        this.initInfiniteScroll();
    },

    initTemplates: function(){
        this.typetag_tmp = _.template($('#type-tag').html());
        this.tagtemp = _.template($('#filter-tag').html());
        for(var key in this.filters){
            if(["skills","countries","issues"].indexOf(key)>-1){
                this.initFilters(this, key, this.tagtemp);
            }
        }
    },

    initFilters: function(that, items, templ){
        var cookie = $.cookie('tagfilters');
        if(typeof cookie != 'undefined'){
            that.filters = cookie;
        }
        _.each(window.ahr[items], function(item){
            var activeFlag = ' ';
            if(_.contains(that.filters[items], item.pk)){
                 activeFlag = 'btn-success';
            }
            $('.row.btn-group-sm.'+items).append(templ({filtertag:item.value, active:activeFlag}));
        });
    },

    updateTagsfilter: function(that, ev){
        a=$(ev.currentTarget.parentElement.parentElement).attr("item_title");
        ar = that.filters[a];
        data = window.ahr[a];
        var tagData = _.find(data, function(test){
            return (test.value == ev.currentTarget.textContent);
        });
        if(tagData) {
            if(_.contains(ar, tagData.pk)){
                that.filters[a] = _.filter(ar, function(item){
                   return item != tagData.pk;
                });
                $(ev.currentTarget).removeClass('btn-success');
            } else {
                that.filters[a].push(tagData.pk);
                $(ev.currentTarget).addClass('btn-success');
            }
        }
        $.cookie('tagfilters',that.filters);
    },

    updateTypefilter: function(that, ev){
        that.filters.types.length = 0;
        var item_type = ev.currentTarget.getAttribute('item_type');
        if(that.types[item_type]) {
            that.filters.types.push(that.types[item_type]);
        }
    },

    setFilterType: function(ftype){
        $('.filter-type').removeClass('btn-success');
        $('.filter-type.'+ftype).addClass('btn-success');
    },

    search: function(){
        this.filters.search = $('#q').val();
        this.setFilterNone();
        this.setFilterKeys();
        this.resetMarket();
    },

    filterKeySearch: function(ev){
        ev.preventDefault();
        this.search();
        return false;
    },

    itemTypesfilter: function(ev){
        this.updateTypefilter(this,ev);
        this.resetMarket();
    },

    tagsfilter: function(ev){
        this.updateTagsfilter(this,ev);
        this.setFilterType("custom");
        this.resetMarket();
    },
    show_dropdown:function(ev){
        ev.preventDefault();
        var item_id = ev.currentTarget.getAttribute('item_id');
        $('#dropdownMenu'+item_id).trigger('click');
        return false;
    },

    private_message: function(ev){
        var username = ev.currentTarget.getAttribute('owner');
        var item_id = ev.currentTarget.getAttribute('item_id');
        var msgsub = 'Re: '+$('.marketitem_title',$('.market-item-card[item_id='+item_id+']')).text();
        this.message_widget.show(username,msgsub,'',true);
        },

    resetitemrate:function(item_id, rate){
        try{
            $(".numstars[item_id="+item_id+"]").rateit('value',rate);
        }catch(err){
            $.noop();
        }
    },

    recommend: function(ev){
        var title = ev.currentTarget.getAttribute('title');
        $('#recsub').val($('#currentusername').text()+' recommends :'+ title);
        $('#recsub').attr('readonly',true);
        var href = '<a href="'+window.location+'">'+ title +'</a>';
        $('#recmessage').val($('#currentusername').text()+ ' recommend you have a look at this post by '+ ev.currentTarget.getAttribute('owner')+' \r\n'+ href );
        $('#touser').val('');
        $('#recommenddialog').modal('show');
    },

    deleteItem: function(ev){
        var that = this;
        if(confirm('Are you sure you want to delete this item?')){
            var item_id = ev.currentTarget.getAttribute('item_id');
            var dfrd = $.ajax({
                url:window.ahr.app_urls.deletemarketitem+item_id,
            });
            dfrd.done(function(data){
                that.alert('Item deleted','#infobar');
                $(".item-wrap[item_id='"+ item_id + "']").remove();
                that.refreshScrollElements();
            });
        }
        //that.msnry.layout();
        return(false);
    },

    editItem: function(ev){
        var that = this;
        var id = ev.currentTarget.getAttribute('item_id');
        $.getJSON(window.ahr.app_urls.getuseritem+id,function(item){
            if(item[0].fields.item_type == "request"){
                that.requestdialog.edit(item);
                that.requestdialog.showModal();
            }else{
                that.offerdialog.edit(item);
                that.offerdialog.showModal();
            }
        });
    },

    init: function(filters){
        $.cookie.json = true;

        this.default_filters = window.ahr.clone(filters);
        this.requestdialog = window.ahr.request_form_dialog.initItem(false);
        this.offerdialog = window.ahr.offer_form_dialog.initItem(false);
        this.message_widget = window.ahr.messagedialog_widget.initWidget('body', '#infobar');
        this.rate_widget = window.ahr.rate_form_dialog.initWidget('body', this.resetitemrate);
        this.report_dialog = window.ahr.report_dialog.initWidget('body');
        this.recommend_dialog = window.ahr.recommend_widget.initWidget(window.ahr.username);
        this.marketitemdialog = window.ahr.marketitem_dialog.initWidget();
        this.item_tmp = _.template($('#item_template').html());

        this.filters = filters;
        this.initTemplates(filters);
        this.filters.search=$('#q').val();
        this.delegateEvents(_.extend(this.events,{
            'click .item_container': 'showItem',
            'click .tagbutton': 'tagsfilter',
            'click #searchbtn': 'search',
            'click .filter-type': 'changeFilterType',
            'click .item-type': 'itemTypesfilter',
            'click #create_offer': 'create_offer',
            'click #create_request': 'create_request',
            'click .itemactions' : 'show_dropdown',
            'click .private_message' : 'private_message',
            'click .recommend': 'recommend',
            'click .delete' : 'deleteItem',
            'click .edit' : 'editItem',
            'submit': 'filterKeySearch'
        }));
    }

});


