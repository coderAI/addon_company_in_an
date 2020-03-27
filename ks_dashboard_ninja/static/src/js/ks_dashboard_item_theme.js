odoo.define('ks_dashboard_ninja_list.ks_dashboard_item_theme', function (require) {
    "use strict";

    var core = require('web.core');
    var common = require('web.form_common');



    var QWeb = core.qweb;


    var KsDashboardTheme = common.AbstractField.extend({

        events: _.extend({}, common.AbstractField.prototype.events, {
            'click .ks_dashboard_theme_input_container' : 'ks_dashboard_theme_input_container_click',
        }),

        start: function() {
            this.on("change:effective_readonly", this, function(){ this.render_value()});
            return this._super();
        },

        render_value: function () {
            var self = this,value = self.get_value();
            self.$el.empty();
            var $view = $(QWeb.render('ks_dashboard_theme_view'));
            if(value){
                $view.find("input[value='"+value+"']").prop("checked", true);
            }
            self.$el.append($view)

            if (self.get('effective_readonly')) {
                this.$el.find('.ks_dashboard_theme_view_render').addClass('ks_not_click');
            }

        },

        ks_dashboard_theme_input_container_click : function(e){
            var self = this;
            var $box = $(e.currentTarget).find(':input');
            if ($box.is(":checked")) {
              self.$el.find('.ks_dashboard_theme_input').prop('checked',false)
              $box.prop("checked", true);
            } else {
              $box.prop("checked", false);
            }
            self.set_value($box[0].value);
        },

    });
    core.form_widget_registry.add('ks_dashboard_item_theme', KsDashboardTheme);

    return {
        KsDashboardTheme: KsDashboardTheme
    };

});

