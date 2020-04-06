odoo.define('mb_sale_invoice.form_widgets', function (require) { "use strict";
    var core = require('web.core');
    var Model = require('web.Model');
    var QWeb = core.qweb;
    var FieldChar = core.form_widget_registry.get('char');

    var AudioField = FieldChar.extend({
		multi_selection: true,
		init: function() {
	        this._super.apply(this, arguments);
	    },
	    start: function()
	    {
	    	this._super.apply(this, arguments);
	    	var self=this;
	    	var audio_template = QWeb.render("AudioField", {widget: this});
	    	this.$el.replaceWith(audio_template.replace("url_field", self.el.innerText));
	   },
	});
	core.form_widget_registry.add('char_audio_field', AudioField);
	return AudioField;
});
