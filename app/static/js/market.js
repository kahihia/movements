$(function () {
  var MarketFilterView = Backbone.View.extend({
    type: '',
    regions: [],
    skills: [],

    events: {
      'click .type-menu a': 'setTypeFilter',
      'click .region-filter a': 'setRegionFilter',
      'click .skill-filter a': 'setSkillsFilter'
    },

    initialize: function() {
      var $skills = this.$el.find('a.skills');
      var $container = $skills.parent().find('.popover-container');
      $.get(window.ahr.app_urls.getSkills, function (data) {
        $skills.popover({
        title: '',
        html: true,
        content: _.template(
              $('#skill-filter-list-template').html(),
              {skills: data}),
          container: $container,
          placement: 'bottom'
        });
      });

      var $regions = this.$el.find('a.regions');
      $container = $regions.parent().find('.popover-container');
      $regions.popover({
        title: '',
        html: true,
        content: _.template($('#region-filter-list-template').html())(),
        container: $container,
        placement: 'bottom'
      });
    },

    toggleFilterState: function(ev) {
      ev.preventDefault();
      var $target = $(ev.currentTarget);
      $target.toggleClass('selected');
      return {
        id: $target.data('id'),
        selected: $target.hasClass('selected'),
        value: $target.data('filter')
      };
    },

    setSkillsFilter: function (ev) {
      var skill = this.toggleFilterState(ev);
      if (skill.selected) {
        this.skills.push(skill.value);
      } else {
        this.skills = $.grep(this.skills, function (value) {
          return value != skill.value;
        });
      }
      this.trigger('filter');
    },

    setRegionFilter: function(ev) {
      this.toggleFilterState(ev);
      this.trigger('filter');
    },

    setTypeFilter: function(ev) {
      ev.preventDefault();
      this.$el.find('.type-menu li.active').removeClass('active');
      var $filterLink = $(ev.currentTarget);
      $filterLink.parents('li').addClass('active');
      this.type = $filterLink.data('filter');
      this.trigger('filter');
    },

    setFilter: function(data) {
      if (this.type) {
        data.types = this.type;
      }
      if (this.skills) {
        data.skills = this.skills;
      }
      console.log(data);
    }
  });

  var PaginationView = Backbone.View.extend({
    el: '#pagination',
    marketView: null,
    pageSize: null,
    pageRange: null,
    pageActive: null,
    events: {
      "click .prev-page": "getPage",
      "click .page": "getPage",
      "click .next-page": "getPage"
    },
    template: _.template($("#pagination_template").html()),

    getPage: function (e) {
      var that = this;
      e.preventDefault();
      var targetPage = $(e.currentTarget).data('page');
      var request = this.marketView.loadPage(targetPage);
      request.done(function () {
        that.render();
      });
    },
    updatePageState: function () {
      this.pageCount = this.marketView.pageCount;
      this.pageActive = this.marketView.pageActive;
      this.pageSize = this.marketView.pageSize;
    },

    initialize: function (options) {
      this.marketView = options.marketView;
      this.pageSize = options.pageSize;
      this.pageRange = options.pageRange;
      this.pageActive = options.pageActive;
      this.init();
    },

    render: function () {
      this.updatePageState();
      if (this.pageCount <= this.pageRange) {
        this.pageRange = this.pageCount;
      }
      var range = Math.floor(this.pageRange / 2);
      var navBegin = this.pageActive - range;
      if (this.pageRange % 2 == 0) {
        navBegin++;
      }
      var navEnd = this.pageActive + range;


      var leftDots = true;
      var rightDots = true;


      if (navBegin <= 2) {
        navEnd = this.pageRange;
        if (navBegin == 2) {
           navEnd++;
        }
        navBegin = 1;
        leftDots = false;
      }

      if (navEnd >= this.pageCount - 1) {
        navBegin = this.pageCount - this.pageRange + 1;
        if (navEnd == this.pageCount - 1) {
           navBegin--;
        }
        navEnd = this.pageCount;
        rightDots = false;
      }

      this.$el.html(this.template({
        link: this.link,
        pageCount: this.pageCount,
        pageActive: this.pageActive,
        navBegin: navBegin,
        navEnd: navEnd,
        leftDots: leftDots,
        rightDots: rightDots
      }));
      return this;
    },
    init: function () {
      var that = this;
      this.pageActive = 1;
      var request = this.marketView.loadPage(1);
      request.done(function () {
        return that.render();
      });
    },
  });

  var MarketView = window.ahr.market.MarketBaseView.extend({
    types: {
      "Offers": "offer",
      "Request": "request"
    },

    events: {
      'click .market-place-item .item-menu': 'showMenuItem',
      'click .item-action-menu a': 'itemAction'
    },

    initialize: function (options) {
      this.item_type = 'item';
      this.getMarketItems = ahr.app_urls.getMarketItems;
      this.item_tmp = _.template($('#item_template').html());
      this.init(options.filterView);
      this.item_menu_template = _.template($('#item-menu-template').html());
      this.closeDialog = new ahr.CloseItemDialogView();
      this.reportDialog = new ahr.ReportPostView();
      return this;
    },

    createItemPopover: function($link) {
      var $container = $link.parent();
      var $itemContainer = $link.parents('.market-place-item');
      var toggled = {
        hide: $itemContainer.data('hidden'),
        stick: $itemContainer.data('stick')
      };
      var content = this.item_menu_template({
        hasEdit: $itemContainer.data('has-edit'),
        toggled: toggled
      });
      $link.popover({
        title: '',
        html: true,
        content: content,
        container: $container,
        placement: 'bottom'
      });
      $link.popover('show');
      $link.data('popover-made', true);
    },

    showMenuItem: function(ev) {
      var $link = $(ev.currentTarget);
      if ($link.data('popover-made')) {
        return;
      } else {
        ev.preventDefault();
        this.createItemPopover($link);
      }
    },

    setItemAttibute: function($container, attribute, value) {
      var data = {};
      data[attribute] = value;
      $.ajax({
        url: $container.data('attributes-url'),
        method: 'POST',
        context: this,
        data: data
      });
      $container.data(attribute, value);
    },

    itemAction: function(ev) {
      ev.preventDefault();
      var $link = $(ev.currentTarget);
      var action = $link.data('action');
      var $container = $link.parents('.market-place-item');
      var pk = $container.data('item-id');
      var itemType = $container.data('item-type');
      var that = this;
      var refresh = function () {
        that.initInfiniteScroll();
      }

      var remakePopover = false
      if (action === 'close') {
        var closeUrl = $container.data('close-url');
        this.closeDialog.close(pk, itemType, closeUrl, refresh);
      } else if (action === 'report') {
        this.reportDialog.showReport($container.data('report-url'));
      } else if (action === 'hide') {
        this.setItemAttibute($container, 'hidden', !$container.data('hidden'))
        remakePopover = true;
      } else if (action === 'stick') {
        this.setItemAttibute($container, 'stick', !$container.data('stick'))
        remakePopover = true;
      }

      var $popover = $container.find('.item-menu');
      if (remakePopover) {
        $popover.popover('destroy');
        $popover.data('popover-made', false);
      } else {
        $popover.popover('toggle');
      }
    }
  });

  window.ahr.market = window.ahr.market || {};
  window.ahr.market.initMarket = function (filters) {
    var filterView = new MarketFilterView({el: '#exchange-filters'});
    //var pagination = new PaginationView({'marketView': market});
    var market = new MarketView({el: '#itemandsearchwrap', filterView: filterView});
    // market.initInfiniteScroll();
    var pagination = new PaginationView({
      marketView: market,
      pageRange: 3,
      pageActive: 1
    });
    filterView.on('filter', function () {
      pagination.init();
    });
    document.title = window.ahr.string_constants.exchange;
  };

});
