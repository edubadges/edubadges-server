var _ = require('underscore');
var assign = require('object-assign');
var EventEmitter = require('events').EventEmitter;

var FormConfigStore = assign({}, EventEmitter.prototype);

FormConfigStore.genericFormTypes = function(){
  return [
    'IssuerCreateUpdateForm',
    'BadgeClassCreateUpdateForm',
    'BadgeInstanceCreateUpdateForm',
    'EarnerBadgeImportForm',
    'EarnerCollectionCreateForm',
    'EarnerCollectionEditForm',
    'BadgrbookDefaultIssuerForm',
  ];
}

FormConfigStore.getConfig = function(formType, overrides, context){
  if (!overrides)
    overrides = {};
  if (!context)
    context = {};

  function contextGet(key, defaultValue){
    if (context.hasOwnProperty(key))
      return context[key];
    return defaultValue;
  }

  var configDefaults = {
    IssuerCreateUpdateForm: {
      formId: overrides['formId'] || "IssuerCreateUpdateForm",
      fieldsMeta: {
        name: {inputType: "text", label: "Issuer Name", required: true},
        description: {inputType: "textarea", label: "Issuer Description", required: true},
        url: {inputType: "text", label: "Website URL", required: true},
        email: {inputType: "text", label: "Contact Email", required: true},
        image: {inputType: "image", label: "Logo (Square PNG)", required: false, filename: "issuer_logo.png"}
      },
      defaultValues: {
        name: "",
        description: "",
        url: "",
        email: "",
        image: null,
        imageData: null,
        actionState: "ready",
        message: ""
      },
      columns: [
        { fields: ['image'], className:'col-xs-5 col-sm-4 col-md-3' },
        { fields: ['name', 'description', 'url', 'email'], className:'col-xs-7 col-sm-8 col-md-9' }
      ],
      apiContext: {
        formId: overrides['formId'] || "IssuerCreateUpdateForm",
        apiCollectionKey: "issuer_issuers",
        actionUrl: "/v1/issuer/issuers",
        method: "POST",
        successHttpStatus: [200, 201],
        successMessage: "New issuer created"
      }
    },

    BadgeClassCreateUpdateForm: {
      formId: overrides['formId'] || "BadgeClassCreateUpdateForm",
      fieldsMeta: {
        name: {inputType: "text", label: "Badge Name", required: true},
        description: {inputType: "textarea", label: "Badge Description", required: true},
        criteria: {inputType: "textarea", label: "Criteria URL or text", required: true},
        image: {inputType: "image", label: "Badge Image (Square PNG)", required: false, filename: "badge_image.png"}
      },
      defaultValues: {
        name: "",
        description: "",
        criteria: "",
        image: null,
        imageData: null,
        actionState: "ready",
        message: ""
      },
      columns: [
        { fields: ['image'], className:'col-xs-5 col-sm-4 col-md-3' },
        { fields: ['name', 'description', 'criteria'], className:'col-xs-7 col-sm-8 col-md-9' }
      ],
      apiContext: {
        formId: overrides['formId'] || "BadgeClassCreateUpdateForm",
        apiCollectionKey: "issuer_badgeclasses",
        actionUrl: "/v1/issuer/issuers/" + contextGet('issuerSlug', '') + "/badges",
        method: "POST",
        successHttpStatus: [200, 201],
        successMessage: "New badge class created"
      }
    },
    BadgeInstanceCreateUpdateForm: {
      formId: overrides['formId'] || "BadgeInstanceCreateUpdateForm",
      fieldsMeta: {
        email: {inputType: "text", label: "Recipient Email", required: true},
        evidence: {inputType: "text", label: "Evidence URL", required: false},
        create_notification: {inputType: "checkbox", label: "Notify earner by email", required: false}
      },
      defaultValues: {
        email: "",
        evidence: "",
        create_notification: false,
        actionState: "ready",
        message: ""
      },
      columns: [
        { fields: ['email', 'evidence', 'create_notification'], className:'col-xs-12' }
      ],
      apiContext: {
        formId: overrides['formId'] || "BadgeInstanceCreateUpdateForm",
        apiCollectionKey: "issuer_badgeinstances",
        actionUrl: "/v1/issuer/issuers/" + contextGet('issuerSlug', '') + "/badges/" + contextGet('badgeClassSlug', '') + '/assertions',
        method: "POST",
        successHttpStatus: [200, 201],
        successMessage: "Badge successfully issued."
      }
    },
    EarnerBadgeImportForm: {
      formId: "EarnerBadgeImportForm",
      helpText: "Fill out one of the following fields to upload your badge. Usually, the baked badge image is available.",
      fieldsMeta: {
        image: {inputType: "image", label: "Badge Image", required: false, filename: "earned_badge.png"},
        url: {inputType: "text", label: "Assertion URL", required: false},
        assertion: {inputType: "textarea", label: "Assertion JSON", required: false}
      },
      defaultValues: {
        image: null,
        imageData: null,
        url: contextGet('url', ''),
        assertion: "",
        actionState: "ready",
        message: ""
      },
      columns: [
        { fields: ['image'], className:'col-xs-5 col-sm-4 col-md-3' },
        { fields: ['url', 'assertion'], className:'col-xs-7 col-sm-8 col-md-9' }
      ],
      apiContext: {
        formId: overrides['formId'] || "EarnerBadgeImportForm",
        apiCollectionKey: "earner_badges",
        actionUrl: "/v1/earner/badges",
        method: "POST",
        successHttpStatus: [200, 201],
        successMessage: "Badge successfully imported."
      }
    },
    EarnerCollectionCreateForm: {
      formId: overrides['formId'] || "EarnerCollectionCreateForm",
      fieldsMeta: {
        name: {inputType: "text", label: "Name", required: true},
        description: {inputType: "textarea", label: "Description", required: false}
      },
      defaultValues: {
        name: "",
        description: "",
        actionState: "ready",
        message: ""
      },
      columns: [
        { fields: ['name', 'description'], className:'col-xs-12' },
      ],
      apiContext: {
        formId: overrides['formId'] || "EarnerCollectionCreateForm",
        apiCollectionKey: "earner_collections",
        actionUrl: "/v1/earner/collections",
        method: "POST",
        successHttpStatus: [200, 201],
        successMessage: "Collection successfully created."
      }
    },
    EarnerCollectionEditForm: {
      formId: overrides['formId'] || "EarnerCollectionEditForm",
      fieldsMeta: {
        name: {inputType: "text", label: "Name", required: true},
        description: {inputType: "textarea", label: "Description", required: false}
      },
      defaultValues: {
        name: contextGet('collection',{name:''}).name,
        description: contextGet('collection',{description:''}).description,
        actionState: "ready",
        message: ""
      },
      columns: [
        { fields: ['name', 'description'], className:'col-xs-12' },
      ],
      apiContext: {
        formId: overrides['formId'] || "EarnerCollectionEditForm",
        apiCollectionKey: "earner_collections",
        actionUrl: "/v1/earner/collections/" + contextGet('collection', {slug:''}).slug,
        method: "PUT",
        successHttpStatus: [200],
        successMessage: "Collection successfully edited."
      }
    },
    BadgrbookDefaultIssuerForm: {
      formId: overrides['formId'] || "BadgrbookDefaultIssuerForm",
      fieldsMeta: {
        default_issuer: {inputType: "text", label: "Default Issuer Slug", required: true},
      },
      defaultValues: {
        default_issuer: "",
      },
      apiContext: {
        formId: overrides['formId'] || "BadgrbookDefaultIssuerForm",
        actionUrl: "/v1/badgrbook/defaultissuer/:tool_guid",
        method: "PUT",
        successHttpStatus: [200],
        successMessage: "Default issuer saved."
      }
    },
  };

  var configData = configDefaults[formType] || {};
  return _.defaults(overrides, configData);
};


module.exports = {
  genericFormTypes: FormConfigStore.genericFormTypes,
  getConfig: FormConfigStore.getConfig
}
