odoo.define('ks_dashboard_ninja_list.ks_color_picker', function (require) {
    "use strict";


    var core = require('web.core');
    var common = require('web.form_common');


    var QWeb = core.qweb;


//    var KsColorPicker = common.AbstractField.extend(common.ReinitializeFieldMixin,{
//
////      To render preview item again on main page.
//        start: function() {
//            this.on('change:value',this.field_manager.fields.ks_preview,this.preview_change);
//            this.on("change:effective_readonly", this, function(){ this.render_value()});
//
//            return this._super();
//        },
//
//        preview_change : function(e){
//            this.render_value();
//        },
//
//        events: _.extend({}, common.AbstractField.prototype.events, {
//            'change .ks_color_picker': '_ksOnColorChange',
//            'change .ks_color_opacity': '_ksOnOpacityChange',
//            'input .ks_color_opacity': '_ksOnOpacityInput'
//        }),

     var KsColorPicker = common.AbstractField.extend({

//        To render preview item again on main page.
        start: function() {
            this.on('change:value',this.field_manager.fields.ks_preview,this.preview_change);
            this.on("change:effective_readonly", this, function(){ this.render_value()});

            return this._super();
        },

        preview_change : function(e){
            this.render_value();
        },

        supportedFieldTypes: ['char'],
//        jsLibs: ['/ks_dashboard_ninja/static/lib/js/color-polyfill.js'],

        events: _.extend({}, common.AbstractField.prototype.events, {
            'move.spectrum .ks_color_picker': '_ksOnColorMove',
            'change.spectrum .ks_color_picker': '_ksOnColorChange',
            'change .ks_color_opacity': '_ksOnOpacityChange',
            'input .ks_color_opacity': '_ksOnOpacityInput'
        }),


        render_value: function () {
            var self = this,value = self.get_value(),ks_color_value,ks_color_opacity;
            self.$el.empty();
            if (value) {
                ks_color_value = value.split(',')[0];
                ks_color_opacity = value.split(',')[1];
            }
            ;
            var $view = $(QWeb.render('ks_color_picker_opacity_view', {
                ks_color_value: ks_color_value,
                ks_color_opacity: ks_color_opacity
            }));
            self.$el.append($view)

            self.$el.find(".ks_color_picker").spectrum({
            color: ks_color_value,
            showInput: true,
            hideAfterPaletteSelect:true,
            clickoutFiresChange: true,
            showInitial: true,
            preferredFormat: "rgb",
            });
            if (self.get('effective_readonly')) {
                self.$el.find('.ks_color_picker').addClass('ks_not_click');
                self.$el.find('.ks_color_opacity').addClass('ks_not_click');
                self.$el.find('.ks_color_picker').spectrum("disable");
            }
            else{
                self.$el.find('.ks_color_picker').spectrum("enable");
            }
        },

        _ksOnColorMove : function(e, tinycolor){
            console.log(tinycolor.toHexString());
        },


        _ksOnColorChange: function (e, tinycolor) {
            this.set_value(tinycolor.toHexString().concat("," + this.get_value().split(',')[1]));
        },


        _ksOnOpacityChange: function (event) {
            this.set_value(this.get_value().split(',')[0].concat("," + event.currentTarget.value));
        },

        _ksOnOpacityInput: function (event) {
            var self = this,color;

            if (self.name == "ks_background_color") {
                color = $('.ks_db_item_preview_color_picker').css("background-color")
                $('.ks_db_item_preview_color_picker').css("background-color", self.get_color_opacity_value(color, event.currentTarget.value))

                color = $('.ks_db_item_preview_l2').css("background-color")
                $('.ks_db_item_preview_l2').css("background-color", self.get_color_opacity_value(color, event.currentTarget.value))

            }
            else if (self.name == "ks_default_icon_color") {
                color = $('.ks_dashboard_icon_color_picker > span').css('color')
                $('.ks_dashboard_icon_color_picker > span').css('color', self.get_color_opacity_value(color, event.currentTarget.value))
            }
            else if (self.name == "ks_font_color") {
                color = $('.ks_db_item_preview').css("color")
                color = $('.ks_db_item_preview').css("color", self.get_color_opacity_value(color, event.currentTarget.value))
            }
        },

        get_color_opacity_value: function (color, val) {
            if (color) {
                return color.replace(color.split(',')[3], val + ")");
            }
            else {
                return false;
            }
        },


    });
    core.form_widget_registry.add('ks_color_dashboard_picker', KsColorPicker);

    return {
        KsColorPicker: KsColorPicker
    };

});

