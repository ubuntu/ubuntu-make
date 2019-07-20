(function() {
    var span = document.querySelector('footer>span');
    if (span) {
      span.innerText = 'Flutter 1.2.3 • 2019-07-11 15:52 • b712a172f9 • stable';
    }
    var sourceLink = document.querySelector('a.source-link');
    if (sourceLink) {
      sourceLink.href = sourceLink.href.replace('/master/', '/b712a172f9/');
    }
  })();
  