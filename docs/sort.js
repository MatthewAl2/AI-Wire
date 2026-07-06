(function(){
  function sortGrid(grid, mode){
    var cards = Array.prototype.slice.call(grid.children);
    cards.sort(function(a, b){
      if(mode === 'importance'){
        var d = parseInt(b.dataset.importance, 10) - parseInt(a.dataset.importance, 10);
        if(d !== 0) return d;
      }
      return parseInt(b.dataset.published, 10) - parseInt(a.dataset.published, 10);
    });
    cards.forEach(function(card){ grid.appendChild(card); });
  }

  document.querySelectorAll('.sort-toggle').forEach(function(toggle){
    var grid = document.getElementById(toggle.getAttribute('data-target'));
    if(!grid) return;
    var buttons = toggle.querySelectorAll('.sort-btn');
    buttons.forEach(function(btn){
      btn.addEventListener('click', function(){
        buttons.forEach(function(b){ b.classList.remove('active'); });
        btn.classList.add('active');
        sortGrid(grid, btn.getAttribute('data-sort'));
      });
    });
  });
})();
