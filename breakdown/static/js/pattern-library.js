document.addEventListener('DOMContentLoaded', function() {

    function dialog() {
        var dialogOpen = document.getElementById('dialogOpen');
        var dialogClose = document.getElementById('dialogClose');
        var dialog = document.getElementById('dialogID');

        if (dialog) {

            dialogPolyfill.registerDialog(dialog);
            // Update button opens a modal dialog
            dialogOpen.addEventListener('click', function() {
              dialog.showModal();
              dialog.classList.add('is-visible');
            });

            // Form cancel button closes the dialog box
            dialogClose.addEventListener('click', function() {
              dialog.close();
              dialog.classList.remove('is-visible');
            });
            
        }
        
    }

    function dropdown() {

        function isDescendant(parent, child) {
            var node = child;
                while (node != null) {

                    if (node == parent) {
                        return true;
                    }

                    node = node.parentNode;

                }

            return false;

        }

        function openTether(target, element) {

            element.classList.add('is-active');

            new Tether({
                element: element,
                target: target,
                attachment: 'top right',
                targetAttachment: 'top right',
                constraints: [
                    {
                      to: document.body,
                      attachment: 'together',
                      pin: true
                    }
                  ]
            });

            Tether.position();

            element.classList.add('is-visible');
            element.classList.add('is-tethered');

        };

        document.addEventListener('click', function(event) {

            var dropdownTrigger = document.getElementById('dropdownTrigger');
            var dropdown = document.getElementById('dropdown');

            if (dropdown) {
                var inDropdown = isDescendant(dropdown, event.target);
                var inTrigger = isDescendant(dropdownTrigger, event.target);

                if (!inDropdown && dropdown.classList.contains('is-active')) {
                    dropdown.classList.remove('is-active');
                    dropdown.classList.remove('is-visible');
                } else if (inTrigger) {
                    openTether(dropdownTrigger, dropdown);
                }
            }
            

        });

    }

    function issuer() {
        var issuer = document.getElementById('issuer');
        var issuerTrigger = document.getElementById('issuerTrigger');

        if (issuer) {
            issuerTrigger.addEventListener('click', function() {
                issuer.classList.toggle('is-expanded');
                issuerTrigger.classList.toggle('icon_-expand');
                issuerTrigger.classList.toggle('icon_-collapse');
            });
        }
        
    }

    function popover() {

        function openPopover(target, element) {

            element.classList.add('is-active');

            new Tether({
                element: element,
                target: target,
                attachment: 'bottom right',
                targetAttachment: 'top right',
                constraints: [
                    {
                      to: 'window',
                      attachment: 'together',
                      pin: true
                    }
                  ]
            });

            Tether.position();

            element.classList.add('is-visible');
            element.classList.add('is-tethered');

        };

        var popoverTrigger = document.getElementById('popoverTrigger');
        var popover = document.getElementById('popover');

        if (popoverTrigger && popover) {

            popoverTrigger.addEventListener('mouseenter', function(event) {
                openPopover(popoverTrigger, popover);
            });

            popoverTrigger.addEventListener('mouseleave', function(event) {
                popover.classList.remove('is-active');
                popover.classList.remove('is-visible');
            });

        }

    }

    function searchinput() {

        var searchContainer = document.querySelector('.search_ fieldset');
        var search = searchContainer.parentNode;
        var searchInput = search.querySelector('input');
        var searchClose = search.querySelector('.search_-x-close');

        if (searchContainer) {

           searchContainer.addEventListener('mouseenter', function() {
               search.classList.add('is-active');
           });

           searchContainer.addEventListener('mouseleave', function() {
               if (!search.classList.contains('is-populated')) {
                   search.classList.remove('is-active');
               }
           });

           searchInput.addEventListener('focus', function() {
               search.classList.add('is-populated');
           });

           searchClose.addEventListener('click', function() {
               search.classList.remove('is-active');
               search.classList.remove('is-populated');
               searchInput.value = '';
           }); 

        }

    }

    dialog();
    dropdown();
    issuer();
    popover();
    searchinput();

});