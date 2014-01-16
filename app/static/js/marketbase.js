window.ahr = window.ahr || {};
window.ahr.market = window.ahr.market || {};

window.ahr.market.MarketBaseView = window.ahr.BaseView.extend({
    el: '#market',
    loadingScrollElemets: false,

    create_request: function(){
        this.requestdialog.showModal(true);
    },
    create_offer: function(){
        this.offerdialog.showModal(true);
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
        var id = ev.currentTarget.getAttribute('item_id');
        window.location = this.viewurl+id;
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

    setItems: function(page){
        var that = this;
        var dfrd = that.getItems(0+(10*page),
                    10+(10*page),
                    this.filters,
                    this.getitemfromto);

        dfrd.done(function(data){
            _.each(data, function(item){
                item.fields.pk = item.pk;
                var item_html = that.item_tmp(item.fields);
                $('#marketitems').append(item_html);
            });
	    
            var $container = $('#marketitems');
            $container.masonry({
                itemSelector: '.market-place-item'
            });
	    that.afterset();

        });

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
        $('#marketitems').empty();
        window.location.hash="";
        this.setItems(0);
        this.setpagecoutner(this.filters, this.itemcount_url);
    },

    setpagecoutner: function(filters, aurl){
        $(".marketitems.pagination").empty();
        var cdfrd = this.getItemsCount(filters,aurl);
        cdfrd.done(function(data){
            var pages = Math.ceil(data.count/10);
            for(i=1;i<=pages;i++){
                $(".marketitems.pagination").append("<li><a class='itempage' page='"+i+"' href='#p"+i+"'>"+i+"</a></li>");
            }
        });
    },

    initTemplates: function(){
        this.typetag_tmp = _.template($('#type-tag').html());
        this.tagtemp = _.template($('#filter-tag').html());
        for(var key in this.filters){
            if(["skills","countries","issues"].indexOf(key)>-1){
                this.initFilters(this, key, this.tagtemp);
            }
        }
        this.initTypeTags(this.types, this.typetag_tmp);
    },

    initFilters: function(that, items, templ){
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
    },

    updateTypefilter: function(that,ev){
        var ind = that.filters.types.indexOf(that.types[ev.currentTarget.textContent]);
        if(ind<0){
            that.filters.types.push(that.types[ev.currentTarget.textContent]);
            $(ev.currentTarget).addClass('btn-success');
        }else{
            that.filters.types.splice(ind,1);
            $(ev.currentTarget).removeClass('btn-success');
        }
    },

    initTypeTags: function(types,tmp){
        for(var item in types){
            $('.typetags').append(tmp({typetag:item}));
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
        $(".numstars[item_id="+item_id+"]").rateit('value',rate);
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
            });
        }
        return(false);
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
      // Trigger for scrolls within 20 pixels from page bottom
      return pageHeight - viewportHeight - scrollHeight < 30;
    },

    initInfiniteScroller: function(){
        var that = this;
        $(window).scroll(function() {
            if(!that.loadingScrollElemets && that.levelReached() ) {
                that.loadingScrollElemets = true;
                console.log("load some more guys");
                var dfrd = that.getItems(0,
                            10,
                            that.filters,
                            that.getitemfromto);

                var itemsToAppend = [];
                dfrd.done(function(data){
                    _.each(data, function(item){
                        item.fields.pk = item.pk;
                        var item_html = that.item_tmp(item.fields);
                        itemsToAppend.push(item_html);
                        $('#marketitems').append(item_html);
                    });

                    if(itemsToAppend.length > 0){
                        var container = document.querySelector('#marketitems');
                        var msnry = new Masonry( container );
                        _.each(itemsToAppend, function(elem){
                            msnry.appended( elem );
                        });
                        msnry.layout();
                    }
                    that.loadingScrollElemets = false;
                });
            }
        });
    },
    
    init: function(filters){
        this.default_filters = window.ahr.clone(filters);

        this.requestdialog = window.ahr.request_form_dialog.initItem(false);
        this.offerdialog = window.ahr.offer_form_dialog.initItem(false);
        this.message_widget = window.ahr.messagedialog_widget.initWidget('#'+this.el.id, '#infobar');
        this.rate_widget = window.ahr.rate_form_dialog.initWidget('#'+this.el.id, this.resetitemrate);
        this.report_dialog = window.ahr.report_dialog.initWidget('body');
        this.recommend_dialog = window.ahr.recommend_widget.initWidget(window.ahr.username);

        this.filters = filters;
        this.initTemplates(filters);
        this.filters.search=$('#q').val();
        this.setpagecoutner(this.filters, this.itemcount_url);
        this.initInfiniteScroller();
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
            'submit': 'filterKeySearch'
        }));
    }

});


