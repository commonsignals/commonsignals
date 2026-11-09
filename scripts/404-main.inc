<main id="top">

  <div class="article-hero">
    <p class="article-eyebrow">Error 404</p>
    <h1>Page not found</h1>
    <p class="article-dek">We couldn't find a page at <span class="nf-path" id="nfPath">this address</span>. It may have moved or been renamed. Search the site below, or go back to the home page.</p>
    <p><a class="btn btn-primary" href="/">Return to the home page</a></p>
  </div>

  <div class="article-shell nf-shell">
    <article class="article-body">
      <form class="nf-search" role="search" action="/sitemap">
        <label for="nfQuery">Search Common Signals</label>
        <input type="search" class="search-input" id="nfQuery" name="q" placeholder="Try a topic, platform or person, e.g. Reddit or Soares" autocomplete="off">
      </form>
      <p class="search-status" id="nfStatus" role="status" aria-live="polite"></p>
      <ul class="search-results" id="nfResults"></ul>
      <p>You can also browse every page in the <a href="/sitemap">sitemap</a>.</p>
    </article>
  </div>

</main>

<script>
// main.js (deferred) defines CSSearch; deferred scripts run before DOMContentLoaded.
document.addEventListener('DOMContentLoaded', function () {
  var input = document.getElementById('nfQuery');

  // Show the missing address and turn it into a starting query.
  var path = decodeURIComponent(location.pathname);
  if (path && path !== '/') {
    document.getElementById('nfPath').textContent = path;
    input.value = CSSearch.words(path).filter(function (w) { return !/^\d+$/.test(w); }).join(' ');
  }

  CSSearch.bind({
    input: input,
    list: document.getElementById('nfResults'),
    status: document.getElementById('nfStatus'),
    eager: true
  });
});
</script>
