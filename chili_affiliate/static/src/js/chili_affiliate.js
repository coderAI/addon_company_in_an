odoo.define('chili_affiliate.web_tree_extension', function (require) {

        "use strict";

     var Listview = require('web.ListView');
     var Formview = require('web.FormView');
     var formats = require('web.formats');

     Listview.Column.include({

         _format: function (row_data, options) {return formats.format_value(row_data[this.id].value, this, options.value_if_empty);}

     });
     Formview.Column.include({

         _format: function (row_data, options) {return formats.format_value(row_data[this.id].value, this, options.value_if_empty);}

     });

    });
