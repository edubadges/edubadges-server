var loginWindow = null;

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function Request() {

    this.poll = false;

    this.activatePoll = function () {
        this.poll = true;
        this.runPoll();
    };

    this.disablePoll = function () {
        this.poll = false;
    };

    this.runPoll = function () {
        var self = this;
        var poll = setTimeout(function () {
            $.ajax({
                url: $('#login-link').attr('check-login'),
                success: function (response) {
                    console.log(response);
                    if(response['loggedin']){
                            self.disablePoll();
                            setTimeout(function(){
                                console.log('in timeout function');
                                if(loginWindow != null) {
                                    loginWindow.close();
                                }
                                window.location =$('#login-link').attr('next-url');

                                },10000);

                    }
                    else{
                        $('#login-link').text('Login bij eduBadges')
                    }

                },
                dataType: "json",
                xhrFields: {
                    withCredentials: true
                },
                complete: function () {
                    if (self.poll == false) {
                        clearTimeout(poll);
                    } else {
                        self.runPoll();
                    }
                }
            })
        }, 333);
    };
}

$(document).ready(function () {
    $.ajaxSetup({
        xhrFields: {
        withCredentials: true
      }
    });
    $request = new Request();
    $request.activatePoll();
    $('#login-link').click(function () {

        loginWindow = window.open($('#login-link').attr('href'));
        return false;

    })
});