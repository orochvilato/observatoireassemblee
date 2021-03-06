var infScroll;
var elem = document.getElementById('deputes-liste');

function setInfiniteScroll(urlupdate){
  if (infScroll!=undefined) {
      elem.innerHTML = "";
      infScroll.destroy()
  }
  var args='gp='+deputes_groupe+'&tr='+deputes_tri+'&di='+deputes_dir+'&txt='+deputes_searchtext+'&rg='+deputes_region+'&top='+deputes_top;
  if (urlupdate) {
      window.history.pushState({},"","?"+args);
  }
  infScroll = new InfiniteScroll( elem, {
  // options
  path: 'deputes/ajax/{{#}}?'+args,
  checkLastPage: '.pagination__next',
  append: '.depute-item',
  history: false,
  prefill: true
  });
}
var groupesel = document.getElementById("deputes-groupe-filter");
groupesel.addEventListener("change", function() { deputes_groupe = this.value; setInfiniteScroll(); });
var regionsel = document.getElementById("deputes-region-filter");
regionsel.addEventListener("change", function() { deputes_region = this.value; setInfiniteScroll(); });
var topsel = document.getElementById("deputes-top-filter");
topsel.addEventListener("change", function() { deputes_top = this.value; setInfiniteScroll(); });
var sortsel = document.getElementById("deputes-sort");
sortsel.addEventListener("change", function() { deputes_tri = this.value; setInfiniteScroll(); });
var dirsel = document.getElementById("deputes-sortdir");
dirsel.addEventListener("change", function() { deputes_dir = this.value; setInfiniteScroll(); });
var search = document.getElementById("deputes-searchbutton");
function launchSearch() {
        deputes_searchtext = document.getElementById("deputes-searchtext").value;
        setInfiniteScroll(); 
}
document.getElementById("deputes-searchtext").addEventListener("change", function(e) {
    deputes_searchtext = this.value;
});
document.getElementById("deputes-search").addEventListener("keypress", function(e) {
     if ((e.which && e.which == 13) || (e.keyCode && e.keyCode == 13)) {
          e.preventDefault();
          launchSearch();
     }
});
