(function (global) {

  var CreatePostView = Backbone.View.extend({
    MAX_FILESIZE: 3,
    UPLOAD_MIMETYPES: 'image/png,image/jpg,image/jpeg',
    events: {
      'click .select-checkbox': 'checkClick',
      'submit': 'submitForm'
    },
    initialize: function() {
      this.fallback = false;
      this.loaderHtml = '<div class="blocker">' + _.template($('#loader-template').html())() + '</div>';
      var that = this;
      this.dz = new Dropzone(this.el, {
        paramName: "images",
        url: document.location.pathname,
        maxFilesize: this.MAX_FILESIZE,
        uploadMultiple: true,
        autoProcessQueue: false,
        clickable: '.dz-clickable',
        previewsContainer: '.dz-preview-container',
        acceptedFiles: this.UPLOAD_MIMETYPES,
        fallback: function () {
          that.$el.find('.fallback').show();
          that.$el.find('.dz-clickable,.dz-preview').hide();
          that.fallback = true;
        },
        addRemoveLinks: true
      });
    },
    checkClick: function(ev) {
      $(ev.currentTarget).find('input[type="checkbox"]').prop("checked", !$(ev.currentTarget).find('input[type="checkbox"]').prop("checked"));
      $(ev.currentTarget).toggleClass("checked");
    },
    addLoader: function() {
      this.$loader = $(this.loaderHtml);
      this.$el.append(this.$loader)
    },
    removeLoader: function() {
      this.$loader.remove();
      this.$loader = null;
    },
    submitForm: function(ev) {
      if (this.fallback) return;
      ev.preventDefault();
      var hasErrors = false;
      var formData = new FormData(this.$el.get(0));
      _.each(this.dz.files, function(file, ix) {
        if (file.status == 'error') hasErrors = true;
        formData.append('image-' + ix, file);
      }, this);
      if (hasErrors) return;
      this.addLoader();
      $.ajax({
        type: 'post',
        context: this,
        data: formData,
        cache: false,
        contentType: false,
        processData: false,
        success: function(resp) {
          if (resp.success) {
            window.location = resp.redir_url;
            return;
          }
          ahr.applyErrorsToForm(this.$el, resp);
          this.removeLoader();
        }
      });
    }
  });

  global.ahr.initCreatePost = function() {
    new CreatePostView({el: '#create-post-form'});
  };

})(window);
