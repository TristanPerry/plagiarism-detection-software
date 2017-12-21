var urlRegex = /^(https?|ftp):\/\/(((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:)*@)?(((\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5]))|((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.?)(:\d*)?)(\/((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)+(\/(([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)*)*)?)?(\?((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)|[\uE000-\uF8FF]|\/|\?)*)?(\#((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)|\/|\?)*)?$/i
var currentRow = $("#prot_res_table").find("tbody tr:first");
var isAmendingOrder = false;
var numNewProtRes = 0;

// We don't validate this server side
var dailyMod = 23;
var weeklyMod = 4;
var centMod = 0.04;

function hasExtension(fileName, exts) {
    return (new RegExp('(' + exts.join('|').replace(/\./g, '\\.') + ')$')).test(fileName);
}

// TODO Add support for multiple files
function styleFileUploads(element) {
    /*var btn = $('<button class="file">Browse...</button>');
    var txt = $('<span class="file"></span>');
    element.after(txt).after(btn);
    element.css({display:'none'});
    var target = element;
    $(btn).click(function(ev){
      ev.preventDefault();
      $(target).click();
    })
    $(target).change(function(){
      // IE uses a stupid renaming scheme that includes "fake-path"
      var fname = $(target).val();
        console(fname);
      $(txt).html(fname.substr(fname.lastIndexOf('\\')+1));
    });*/
}

function changePrice() {
    if (!isAmendingOrder) {
        $("#orderSummary").show();
        isAmendingOrder = true;
    }
    calculatePrice();
}

function calculatePrice() {
    // TODO Multi currency support
    var totalDaily = (numDaily * dailyMod * centMod);
    var totalWeekly = (numWeekly * weeklyMod * centMod);
    var totalMonthly = (numMonthly * centMod);

    var price = totalDaily + totalWeekly + totalMonthly;
    var explanation = "";

    if( totalDaily > 0 ) {
        explanation += "<li>"+ numDaily +" resources with daily protection = $"+ roundMoney(totalDaily) + "</li>";
    }

    if( totalWeekly > 0 ) {
        explanation += "<li>"+ numWeekly +" resources with weekly protection = $"+ roundMoney(totalWeekly) + "</li>";
    }

    if( totalMonthly > 0 ) {
        explanation += "<li>"+ numMonthly +" resources with monthly protection = $"+ roundMoney(totalMonthly) + "</li>";
    }

    if( price < 3.5 ) {
        price = 3.5;
        explanation += "<li>Minimum order is $3.50 per month.</li>";
    }

    price = roundMoney(price);

    if (typeof currentPrice !== 'undefined') {
        priceDiff = roundMoney(price - currentPrice);

        if (priceDiff > 0) {
            if (isNewOrder) {
                explanation += "<li>$" + priceDiff + " due monthly.</li>";
            } else {
                explanation += "<li>$" + priceDiff + " due today, then $" + price + " due thereafter on your usual payment date.</li>";
            }
        }
    }

    $("#newPrice").html("&dollar;"+price);
    $("#orderBreakdown").html(explanation);
}

function roundMoney( amount ) {
    var rounded = Math.round(amount*100)/100;
    return rounded.toFixed(2);
}

function incrementScanFreq(scanFreq) {
    if (scanFreq == "Daily") {
        numDaily++;
    } else if(scanFreq == "Weekly") {
        numWeekly++;
    } else if(scanFreq == "Monthly") {
        numMonthly++;
    }
    changePrice();
}

function decrementScanFreq(scanFreq) {
    if (scanFreq == "Daily") {
        numDaily--;
    } else if(scanFreq == "Weekly") {
        numWeekly--;
    } else if(scanFreq == "Monthly") {
        numMonthly--;
    }
    changePrice();
}

function changeNewHttpParamNames(html) {
    var thisHtml = $(html);
    thisHtml.find("input[name='new_prot_res_url']").attr("name", "new_prot_res_url_"+numNewProtRes);
    thisHtml.find("select[name='new_pros_res_scan_freq']").attr("name", "new_pros_res_scan_freq_"+numNewProtRes);

    var fileInput = thisHtml.find("input[name='new_prot_res_file']");
    if (fileInput.length > 0) {
        fileInput.attr("name", "new_prot_res_file_" + numNewProtRes);
    }

    numNewProtRes++;
    $("#numNewProtRes").val(numNewProtRes);
    return html;
}

function validateUrl(element) {
    var value = trim(element.val());
    var row = element.parent().parent();
    var firstCell = row.find("td:first");
    firstCell.find("img").remove();
    var scanFreq = element.parent().next().find("select option:selected").val();

    if (urlRegex.test(value)) {
        firstCell.append(tickIcon);
    } else {
        firstCell.append(crossIcon);
    }
}

function addResource(e, loc) {
    incrementScanFreq("Daily");

    var elem = $(e);
    var addTo = elem.parent().parent();

    var htmlText = $("#addProtRes").text();
    var html = $.parseHTML(htmlText)[1];
    html = changeNewHttpParamNames(html);

    var fileElement = $(html).find("input[type=file]");
    if (loc == 'after') {
        addTo.after(html);
    } else {
        addTo.before(html);
    }
    styleFileUploads(fileElement);
}

function editResource(id) {
    var table_row = $("#tr_prot_res_"+id);

    var prot_res_cell = table_row.find("td:first");
    prot_res_cell.find("span").toggle();
    prot_res_cell.find("input[type=name]").toggle();
    prot_res_cell.find("div").toggle();
    prot_res_cell.find("div span").toggle();

    var scan_freq_cell = table_row.find("td:nth-child(4)");
    scan_freq_cell.find("span").toggle();
    scan_freq_cell.find("select").toggle();

    var edit_icon = table_row.find("td:last a.editLink");
    if (edit_icon.find("#backIcon").length === 0) {
        edit_icon.html(backIcon);
    } else {
        edit_icon.html(editIcon);
    }

    changePrice();
}

function deleteResource(id) {
    var row = $("#tr_prot_res_"+id);
    var scanFreq = row.find("td:nth-child(4) select option:selected").val();
    decrementScanFreq(scanFreq);
    row.remove();
}

function deleteNewResource(element) {
    var row = $(element).parent().parent();
    var scanFreq = row.find("td:nth-child(2) select option:selected").val();
    decrementScanFreq(scanFreq);
    row.remove();
}

function bulkAddURLs() {
    $("#bulkImportUrls").show(300);
}

function addBulkUrl(htmlTemplate, url) {
    var html = $.parseHTML(htmlTemplate)[1];
    html = changeNewHttpParamNames(html);
    $(html).find(".new_prot_res_url_single").val(url);

    currentRow.after(html);
    currentRow = currentRow.next();
}

$(document).on("change", ".new_prot_res_url", function () {
    // Clear the file field
    $(this).next().next().remove();
    $(this).next().after(newFileUpload);
});

$(document).on("change", ".new_prot_res_url_single, .new_prot_res_url", function () {
    validateUrl($(this));
});

$(document).on("change", ".new_prot_res_file", function () {
    var fileName = $(this).val();
    var row = $(this).parent().parent();
    var firstCell = row.find("td:first");
    firstCell.find("img").remove();
    var scanFreq = $(this).parent().next().find("select option:selected").val();

    if (hasExtension(fileName, ['.pdf', '.txt', '.pptx', '.doc', '.docx'])) {
        firstCell.append(tickIcon);
    } else {
        firstCell.append(crossIcon);
    }

    // Clear the URL field
    $(this).prev().prev().val('');
});

$(document).on("click keydown focus", ".scanFreqSelect", function() {
    $(this).data('oldValue', $(this).val());
});

$(document).on("change", ".scanFreqSelect", function() {
    var oldVal = $(this).data('oldValue');
    var newVal = $(this).val();

    decrementScanFreq(oldVal);
    incrementScanFreq(newVal);
});

$(function() {
    // replace all file upload elements for styling purposes
    $('input[type="file"]').each(function() {
        styleFileUploads($(this));
    });

    $(".closeButton").click(function() {
        $(this).parent().hide(300);
    });

    $("#sitemapInput").keypress(function() {
        $("#bulkInput").val("");
    });

    $("#sitemapInput").on('paste', function() {
        $("#bulkInput").val("");
    });

    $("#setAllScanFreq").change(function() {
        var newVal = $("#setAllScanFreq option:selected").val();
        $(".scanFreqSelect").each(function() {
            var currVal = $(this).val();
            $(this).val(newVal);

            decrementScanFreq(currVal);
            incrementScanFreq(newVal);
        });
    });

    $("#bulkInput").bind('input propertychange', function() {
        $("#sitemapInput").val("");
    });

    $("#cancelOrderChange").click(function() {
       location.reload();
    });

    $("#bulkImportButton").click(function() {
        var sitemap = trim($("#sitemapInput").val());
        var bulkUrls = trim($("#bulkInput").val());
        var htmlText = $("#addURL").text();

        if (bulkUrls) {
            var allUrls = bulkUrls.split("\n");

            for (var i = 0; i < allUrls.length; i++) {
                addBulkUrl(htmlText, allUrls[i]);
                numDaily++;
            }

        } else {

            $.ajax({
              dataType: "json",
              url: sitemapURL,
              data: {sitemap_url: sitemap},
              async: false,
              success: function(data) {
                    $.each(data, function(index) {
                        addBulkUrl(htmlText, data[index]);
                        numDaily++;
                    });
                }
            });
        }

        changePrice();
        $("#bulkImportUrls").hide();
    });
});