'use strict';

var raw_html_tree = document.getElementById('toc').firstChild.cloneNode(true);

function createSearchable(el) {
  var par = el.parentElement;
  var obj = el.cloneNode(true);

  while(par != raw_html_tree) {
    var clone_parent = par.cloneNode(true);

    while (clone_parent.firstChild != clone_parent.lastChild) {
      clone_parent.removeChild(clone_parent.lastChild);
    }
    console.log("obj.innerHTML: " + obj.innerHTML);
    console.log("clone_parent.firstChild.innerHTML: " + clone_parent.firstChild.innerHTML);
    if (obj.innerHTML != clone_parent.firstChild.innerHTML) 
      clone_parent.appendChild(obj);

    obj = clone_parent;
    par = par.parentElement;
  }

  return {
    searchable: el.innerHTML,
    obj: obj
  };
}

var searchables = [];
Array(...raw_html_tree.getElementsByTagName('a'))
  .forEach(el => searchables.push(createSearchable(el)));

var fuse = new Fuse(searchables, { keys: [ 'searchable' ], includeMatches: true});
var searchBar = document.getElementById('search');
var resultsDiv = document.getElementById('toc');

function updateResults() {
  var ul = document.createElement('ul');
  resultsDiv.innerHTML = '';
  if (searchBar.value == '') {
    resultsDiv.appendChild(raw_html_tree);
    return;
  }
  var results = fuse.search(searchBar.value);


  results.forEach(r => {
    console.log(r)
    var content = r.item.obj
    var last_a = Array.from(r.item.obj.getElementsByTagName('a')).pop()

    r.matches.reverse().every(match => {
      var display_match = match.value;
      if (match.indices.length >= 1) {
        match.indices.sort((a, b) => (b[1]-b[0])-(a[1]-a[0]));
        const indexPair = match.indices[0];
        const matching_slice = match.value.slice(indexPair[0], indexPair[1]+1);
        last_a.innerHTML = match.value.replace(
          matching_slice,
          '<span class="matchHighlight">' + matching_slice + '</span>'
        );
      }
      return true;
    })

    ul.appendChild(content);
    ul.appendChild(document.createElement('br'));
  })
  resultsDiv.appendChild(ul);
}

searchBar.addEventListener('keyup', e => {
  // if user pressed enter
  if (e.keyCode === 13) {
    if (e.shiftKey) {
      window.open(results[0].item.path, '_blank');
    } else {
    window.location.href = results[0].item.path;
    }
    return;
  }
  updateResults();
})

searchBar.addEventListener('change', updateResults);

const searchParams = new URL(window.location.href).searchParams;
searchBar.value = searchParams.get('q');
updateResults();

if (searchParams.has('lucky')) {
  window.location.href = results[0].item.path;
}
