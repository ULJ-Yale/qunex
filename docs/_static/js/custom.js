window.addEventListener('load', function () {
  hideTerminalSig();
  parameterDetails();
  hamburgerScrollingFix();
  extractImgDescriptions();
});

function extractImgDescriptions() {
  /*
  The jQuery script below extracts image descriptions that are "hidden" into
  the alt attribute by the myst_parser Sphinx extension and makes them visible
  by building an HTML figure around them.
  */

  $("main p").has("img").each(function () {
    var figureImg = $(this).find("img");
    figureImg.addClass("figure-img img-fluid rounded");

    var imageAlt = figureImg.attr("alt");
    var figureCaption = $('<figcaption class="figure-caption text-center"></figcaption>').text(imageAlt);
    $(this).append(figureCaption);

    $(this).replaceWith("<figure class='text-center'>" + this.innerHTML + "</figure>"); // centered without figure class
  });
}

function parameterDetails() {
  /*
  Adds code tag to parameter details.
  */
  $("p:contains('Parameters')").next().find("dt").each(function () {
    let contents = $(this).html();
    if (contents.match("--\\S+(?:, -{1,2}\\S+)* \\(.+\\):$") && $(this).parent().prev().hasClass("rubric")) {
      contents = contents.replace(" \(", " (<code>");
      contents = contents.substring(0, contents.length - 2) + "</code>):";
      $(this).html(contents);
    }
  });
}

function hamburgerScrollingFix() {
  // Fixes incorrect hamburger menu scrolling position in responsive mode.

  document.getElementsByClassName("btn-navbar")[0].addEventListener('click', function () {
    document.body.scrollTop = 0; // For Safari
    document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
  });
}

function hideTerminalSig() {
  /*
  Appends .sig class to hide the function's terminal signatures.
   */
  var commandH1Content = jQuery.trim($("h1")[1].innerHTML);

  $("dd p").first("code span").each(function () {
    var spanElement = $(this).find("span:first");
    var spanContent = jQuery.trim(spanElement.text().slice(0, commandH1Content.length));
    if (spanContent == commandH1Content) {
      $(this).addClass("sig");

      $(this).next().has("code span").each(function () {
        $(this).addClass("sig");
      });
    }
  });
}