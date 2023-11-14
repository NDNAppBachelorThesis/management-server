var fwUpdateCompleteUrl;    // Set in HTML


function reportUpdateStatus(boardId, successful) {
    $.ajax({
            type: 'POST',
            url: location.origin  + fwUpdateCompleteUrl.substring(0, fwUpdateCompleteUrl.length - 1) + boardId,
            headers: {
                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
            },
            data: {
                success: successful,
            }
        }
    )
}


window.onload = function () {
    $('form').submit(function (e) {
        e.preventDefault();
        var form = $('#upload_form')[0];
        var formData = new FormData(form);

        var boardRows = document.querySelectorAll(".board-row")

        boardRows.forEach(function (row) {
            var doUpdateDb = row.querySelector(".do-update-cb");

            if (doUpdateDb && doUpdateDb.checked) {
                var rowData = row.dataset;
                console.log("Updating firmware for " + rowData.ip);
                let progressBarElem = $('#progress-bar-' + rowData.id);
                reportUpdateStatus(rowData.id, true)
                return;
                $.when($.ajax({
                    type: 'POST',
                    url: 'http://' + rowData.ip + '/update',
                    data: formData,
                    contentType: false,
                    processData: false,
                    xhr: function () {
                        // Reset colors
                        progressBarElem.removeClass("bg-success", "bg-danger")
                        progressBarElem.addClass("progress-bar-striped")
                        var xhr = new window.XMLHttpRequest();
                        xhr.upload.addEventListener('progress', function (evt) {
                            if (evt.lengthComputable) {
                                var per = evt.loaded / evt.total;
                                $('#progress-text-' + rowData.id).html(Math.round(per * 100) + '%');
                                progressBarElem.css("width", Math.round(per * 100) + '%')
                            }
                        }, false);
                        return xhr;
                    },
                    success: function (d, s) {
                        progressBarElem.addClass("bg-success")
                        progressBarElem.removeClass("progress-bar-striped")
                        reportUpdateStatus(rowData.id, true)
                    },
                    error: function (a, b, c) {
                        progressBarElem.addClass("bg-danger")
                        progressBarElem.removeClass("progress-bar-striped")
                        reportUpdateStatus(rowData.id, false)
                    }
                }))
            }
        });

    })
}
