(function() {
  const DATA_URL = '/wp-content/uploads/race-index.json?v=20260215';
  const TIER_PAGE_SIZE = 20;

  let allRaces = [];
  let currentSort = 'score';
  let displayMode = 'stream'; // 'stream', 'tiers', or 'match'
  let matchScores = {};      // slug → match pct
  let tierVisibleCounts = { 1: TIER_PAGE_SIZE, 2: TIER_PAGE_SIZE, 3: TIER_PAGE_SIZE, 4: TIER_PAGE_SIZE };
  let matchVisibleCount = TIER_PAGE_SIZE;
  let tierCollapsed = { 1: false, 2: false, 3: true, 4: true };

  // Near Me state
  let userLat = null;
  let userLng = null;
  let nearMeRadius = 0; // 0 = off, otherwise miles
  let raceDistances = {}; // slug → distance in miles

  // Compare state
  let compareSlugs = [];    // Array of slug strings, max 4
  let compareMode = false;  // true when showing compare panel

  // Favorites state
  var favorites = JSON.parse(localStorage.getItem('rl-favorites') || '[]');
  var showFavoritesOnly = false;
  function saveFavorites() { localStorage.setItem('rl-favorites', JSON.stringify(favorites)); }

  // Saved filter configs state
  var savedConfigs = [];
  try { savedConfigs = JSON.parse(localStorage.getItem('rl-saved-filters') || '[]'); } catch(e) { savedConfigs = []; }
  var activeSavedIndex = -1;

  var COMPARE_COLORS = [
    { stroke: '#1a1a2e', fill: 'rgba(26,26,46,0.15)' },
    { stroke: '#e63946', fill: 'rgba(230,57,70,0.15)' },
    { stroke: '#3d5a80', fill: 'rgba(61,90,128,0.15)' },
    { stroke: '#6c757d', fill: 'rgba(108,117,125,0.15)' }
  ];

  // Map state
  let mapInstance = null;
  let mapMarkers = [];
  let viewMode = 'list'; // 'list' or 'map'
  let leafletLoaded = false;

  const TIER_NAMES = { 1: 'The Icons', 2: 'Elite', 3: 'Solid', 4: 'Grassroots' };
  const TIER_DESCS = {
    1: 'The definitive road events. World-class fields, iconic courses, bucket-list status.',
    2: 'Established races with strong reputations and competitive fields. The next tier of must-ride events.',
    3: 'Regional favorites and emerging events. Strong local scenes, genuine road racing character.',
    4: 'Up-and-coming events and local rides. Small fields, raw vibes, grassroots road cycling.'
  };
  const US_REGIONS = new Set(['West', 'Midwest', 'South', 'Northeast']);
  const TIER_COLORS_MAP = { 1: '#1a1a2e', 2: '#3d5a80', 3: '#6c757d', 4: '#adb5bd' };

  const SLIDERS = [
    { key: 'distance',      label: 'Distance',      low: 'Quick Spin',       high: 'Ultra Endurance', mapping: [{ field: 'distance', weight: 1.0 }] },
    { key: 'surface',       label: 'Road Surface',   low: 'Smooth Tarmac',    high: 'Mixed Surface',   mapping: [{ field: 'road_surface', weight: 1.0 }] },
    { key: 'climbing',      label: 'Climbing',       low: 'Flat is Fast',     high: 'Mountain Goat',   mapping: [{ field: 'climbing', weight: 1.0 }] },
    { key: 'logistics',     label: 'Logistics',      low: 'Easy Access',      high: 'Remote Start',    mapping: [{ field: 'logistics', weight: 1.0 }] },
    { key: 'competition',   label: 'Competition',    low: 'Just Finish',      high: 'Pro Field',       mapping: [{ field: 'field_depth', weight: 0.6 }, { field: 'race_quality', weight: 0.4 }] },
    { key: 'prestige',      label: 'Prestige',       low: 'Hidden Gem',       high: 'Bucket List',     mapping: [{ field: 'prestige', weight: 1.0 }] },
    { key: 'budget',        label: 'Budget',         low: 'All-In',           high: 'Budget Friendly', mapping: [{ field: 'value', weight: 0.6 }, { field: 'expenses', weight: 0.4, invert: true }] }
  ];

  function noResultsHtml() {
    return '<div class="rl-no-results">No races match your filters.' +
      '<div class="rl-no-results-suggestions">Try removing a filter, selecting a different region, or choosing &ldquo;Any&rdquo; for month.<br>' +
      '<button class="rl-no-results-reset" onclick="document.querySelectorAll(\'#rl-race-search select\').forEach(function(s){s.selectedIndex=0});' +
      'document.querySelectorAll(\'#rl-race-search .rl-slider-input\').forEach(function(s){s.value=3});' +
      'window.dispatchEvent(new Event(\'rl-reset-filters\'));">Reset All Filters</button></div></div>';
  }

  // ── Haversine distance (miles) ──
  function haversineMi(lat1, lng1, lat2, lng2) {
    var R = 3959; // Earth radius in miles
    var dLat = (lat2 - lat1) * Math.PI / 180;
    var dLng = (lng2 - lng1) * Math.PI / 180;
    var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLng/2) * Math.sin(dLng/2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  function computeDistances() {
    raceDistances = {};
    if (userLat === null) return;
    allRaces.forEach(function(r) {
      if (r.lat != null && r.lng != null) {
        raceDistances[r.slug] = Math.round(haversineMi(userLat, userLng, r.lat, r.lng));
      }
    });
  }

  // ── Init ──
  function fetchWithRetry(url, attempts, delay) {
    return fetch(url).then(function(r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    }).catch(function(err) {
      if (attempts <= 1) throw err;
      return new Promise(function(resolve) {
        setTimeout(function() { resolve(fetchWithRetry(url, attempts - 1, delay * 2)); }, delay);
      });
    });
  }

  function init() {
    buildSliders();
    fetchWithRetry(DATA_URL, 3, 1000)
      .then(function(data) {
        allRaces = data;
        populateFilterOptions();
        loadFromURL();
        // Validate compare slugs against loaded data
        var validSlugs = {};
        allRaces.forEach(function(r) { validSlugs[r.slug] = true; });
        compareSlugs = compareSlugs.filter(function(s) { return validSlugs[s]; });
        if (compareSlugs.length < 2) compareMode = false;
        updateFavoritesToggle();
        renderSavedBar();
        render();
        bindEvents();
      })
      .catch(function(err) {
        document.getElementById('rl-tier-container').innerHTML =
          '<div class="rl-no-results">Unable to load race data. Please refresh the page or try again later.</div>';
        console.error('Race index load failed after retries:', err);
      });
  }

  // ── Questionnaire sliders ──
  function buildSliders() {
    var grid = document.getElementById('rl-slider-grid');
    grid.innerHTML = SLIDERS.map(function(s) { return '\
      <div class="rl-slider-row">\
        <span class="rl-slider-label">' + s.label + '</span>\
        <input type="range" min="1" max="5" value="3" id="rl-q-' + s.key + '" aria-label="' + s.label + ': ' + s.low + ' to ' + s.high + '">\
        <div class="rl-slider-endpoints">\
          <span>' + s.low + '</span>\
          <span>' + s.high + '</span>\
        </div>\
      </div>';
    }).join('');
  }

  function getSliderValues() {
    var vals = {};
    SLIDERS.forEach(function(s) {
      vals[s.key] = parseInt(document.getElementById('rl-q-' + s.key).value);
    });
    return vals;
  }

  function computeMatchScore(race, sliderVals) {
    if (!race.scores) return 0;
    var weightedSqDiff = 0;
    var totalWeight = 0;
    SLIDERS.forEach(function(s) {
      var userVal = sliderVals[s.key];
      s.mapping.forEach(function(m) {
        var raceVal = race.scores[m.field] || 1;
        if (m.invert) raceVal = 6 - raceVal;
        var diff = userVal - raceVal;
        weightedSqDiff += m.weight * diff * diff;
        totalWeight += m.weight;
      });
    });
    var maxPossible = totalWeight * 16;
    return Math.round((1 - weightedSqDiff / maxPossible) * 100);
  }

  // ── Match mode ──
  function runMatch() {
    var vals = getSliderValues();
    matchScores = {};
    allRaces.forEach(function(r) {
      matchScores[r.slug] = computeMatchScore(r, vals);
    });
    displayMode = 'match';
    document.getElementById('rl-btn-reset').style.display = '';
    render();
    saveToURL();
  }
  window.runMatch = runMatch;

  function resetMatch() {
    displayMode = 'stream';
    matchScores = {};
    matchVisibleCount = TIER_PAGE_SIZE;
    document.getElementById('rl-btn-reset').style.display = 'none';
    tierVisibleCounts = { 1: TIER_PAGE_SIZE, 2: TIER_PAGE_SIZE, 3: TIER_PAGE_SIZE, 4: TIER_PAGE_SIZE };
    document.querySelectorAll('.rl-display-btn').forEach(function(b) {
      b.classList.toggle('active', b.dataset.display === 'stream');
    });
    render();
    saveToURL();
  }
  window.resetMatch = resetMatch;

  // ── Questionnaire toggle ──
  function toggleQuestionnaire() {
    var body = document.getElementById('rl-q-body');
    var toggle = document.getElementById('rl-q-toggle');
    body.classList.toggle('collapsed');
    toggle.classList.toggle('collapsed');
  }
  window.toggleQuestionnaire = toggleQuestionnaire;

  // ── Near Me ──
  function activateNearMe() {
    var btn = document.getElementById('rl-nearme-btn');
    if (!btn) return;

    if (userLat !== null) {
      // Already have location — toggle off
      userLat = null;
      userLng = null;
      nearMeRadius = 0;
      raceDistances = {};
      btn.classList.remove('active');
      btn.textContent = 'NEAR ME';
      var radiusSel = document.getElementById('rl-nearme-radius');
      if (radiusSel) radiusSel.style.display = 'none';
      currentSort = 'score';
      updateSortButtons();
      render();
      saveToURL();
      return;
    }

    if (!navigator.geolocation) {
      btn.textContent = 'NOT SUPPORTED';
      btn.disabled = true;
      return;
    }

    btn.textContent = 'LOCATING...';
    btn.disabled = true;

    navigator.geolocation.getCurrentPosition(
      function(pos) {
        userLat = pos.coords.latitude;
        userLng = pos.coords.longitude;
        nearMeRadius = 500; // default radius
        computeDistances();
        btn.classList.add('active');
        btn.textContent = 'NEAR ME ✓';
        btn.disabled = false;
        var radiusSel = document.getElementById('rl-nearme-radius');
        if (radiusSel) {
          radiusSel.style.display = '';
          radiusSel.value = '500';
        }
        currentSort = 'nearby';
        updateSortButtons();
        render();
        saveToURL();
      },
      function(err) {
        btn.textContent = 'DENIED';
        btn.disabled = false;
        setTimeout(function() {
          btn.textContent = 'NEAR ME';
        }, 2000);
        console.warn('Geolocation denied:', err.message);
      },
      { timeout: 10000, maximumAge: 300000 }
    );
  }
  window.activateNearMe = activateNearMe;

  function onRadiusChange() {
    var sel = document.getElementById('rl-nearme-radius');
    nearMeRadius = parseInt(sel.value) || 0;
    render();
    saveToURL();
  }
  window.onRadiusChange = onRadiusChange;

  function updateSortButtons() {
    document.querySelectorAll('.rl-sort-btn').forEach(function(b) {
      b.classList.toggle('active', b.dataset.sort === currentSort);
    });
  }

  // ── Map ──
  function loadLeaflet(callback) {
    if (leafletLoaded) { callback(); return; }
    var css = document.createElement('link');
    css.rel = 'stylesheet';
    css.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    document.head.appendChild(css);
    var js = document.createElement('script');
    js.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    js.onload = function() { leafletLoaded = true; callback(); };
    document.head.appendChild(js);
  }

  function initMap() {
    if (mapInstance) return;
    var container = document.getElementById('rl-map-container');
    if (!container) return;
    mapInstance = L.map(container, { scrollWheelZoom: true, zoomControl: true }).setView([30, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 18
    }).addTo(mapInstance);
  }

  function updateMapMarkers() {
    if (!mapInstance) return;
    mapMarkers.forEach(function(m) { mapInstance.removeLayer(m); });
    mapMarkers = [];
    var filtered = sortRaces(filterRaces());
    filtered.forEach(function(race) {
      if (race.lat == null || race.lng == null) return;
      var tierColor = TIER_COLORS_MAP[race.tier] || '#adb5bd';
      var marker = L.circleMarker([race.lat, race.lng], {
        radius: race.tier === 1 ? 8 : race.tier === 2 ? 7 : 6,
        fillColor: tierColor,
        color: '#1a1613',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.85
      });
      var popupHtml = '<div class="rl-map-popup">' +
        '<p class="rl-popup-name">' +
          (race.has_profile
            ? '<a href="' + race.profile_url + '">' + race.name + '</a>'
            : race.name) +
        '</p>' +
        '<p class="rl-popup-meta">' + (race.location || '') +
          (race.month ? ' &middot; ' + race.month : '') + '</p>' +
        '<p class="rl-popup-stats">' +
          (race.overall_score ? '<span class="rl-popup-score">' + race.overall_score + '</span>' : '') +
          (race.distance_mi ? race.distance_mi + ' mi' : '') +
          (race.distance_mi && race.elevation_ft ? ' &middot; ' : '') +
          (race.elevation_ft ? Number(race.elevation_ft).toLocaleString() + ' ft' : '') +
        '</p>' +
        (userLat !== null && raceDistances[race.slug] !== undefined
          ? '<p class="rl-popup-meta">' + raceDistances[race.slug].toLocaleString() + ' mi away</p>'
          : '') +
        (race.rwgps_id
          ? '<p class="rl-popup-route"><a href="https://ridewithgps.com/routes/' + race.rwgps_id + '" target="_blank" rel="noopener">View Route &#x2197;</a></p>'
          : '') +
      '</div>';
      marker.bindPopup(popupHtml, { maxWidth: 280 });
      marker.addTo(mapInstance);
      mapMarkers.push(marker);
    });
  }

  // ── Calendar ──
  var MONTH_NAMES = ['January','February','March','April','May','June',
                     'July','August','September','October','November','December'];

  function renderCalendar() {
    var calContainer = document.getElementById('rl-calendar-container');
    if (!calContainer) return;
    var filtered = sortRaces(filterRaces());
    var byMonth = {};
    MONTH_NAMES.forEach(function(m) { byMonth[m] = []; });
    filtered.forEach(function(r) {
      if (r.month && byMonth[r.month]) byMonth[r.month].push(r);
    });
    var noMonth = filtered.filter(function(r) { return !r.month; });
    var currentMonth = MONTH_NAMES[new Date().getMonth()];
    var html = '';
    MONTH_NAMES.forEach(function(m) {
      var races = byMonth[m];
      if (races.length === 0) return;
      var isCurrent = (m === currentMonth);
      html += '<div class="rl-cal-month' + (isCurrent ? ' rl-cal-now' : '') + '" id="rl-cal-' + m.toLowerCase() + '">' +
        '<div class="rl-cal-month-header">' +
          '<span>' + m.toUpperCase() + '</span>' +
          '<span class="rl-cal-month-count">' + races.length + ' race' + (races.length !== 1 ? 's' : '') + '</span>' +
        '</div>';
      races.forEach(function(r) {
        var nameTag = r.has_profile
          ? '<a class="rl-cal-name" href="' + r.profile_url + '">' + r.name + '</a>'
          : '<span class="rl-cal-name">' + r.name + '</span>';
        var distBadge = '';
        if (userLat !== null && raceDistances[r.slug] !== undefined) {
          distBadge = ' <span class="rl-distance-badge">' + raceDistances[r.slug].toLocaleString() + ' mi</span>';
        }
        html += '<div class="rl-cal-race">' +
          '<span class="rl-tier-badge rl-tier-' + r.tier + '">T' + r.tier + '</span>' +
          '<div class="rl-cal-info">' + nameTag + '<div class="rl-cal-loc">' + (r.location || '') +
            (r.distance_mi ? ' &middot; ' + r.distance_mi + ' mi' : '') + distBadge + '</div></div>' +
          (r.overall_score ? '<span class="rl-cal-score">' + r.overall_score + '</span>' : '') +
        '</div>';
      });
      html += '</div>';
    });
    if (noMonth.length > 0) {
      html += '<div class="rl-cal-month"><div class="rl-cal-month-header"><span>DATE TBD</span>' +
        '<span class="rl-cal-month-count">' + noMonth.length + ' race' + (noMonth.length !== 1 ? 's' : '') + '</span></div>';
      noMonth.forEach(function(r) {
        var nameTag = r.has_profile
          ? '<a class="rl-cal-name" href="' + r.profile_url + '">' + r.name + '</a>'
          : '<span class="rl-cal-name">' + r.name + '</span>';
        html += '<div class="rl-cal-race">' +
          '<span class="rl-tier-badge rl-tier-' + r.tier + '">T' + r.tier + '</span>' +
          '<div class="rl-cal-info">' + nameTag + '<div class="rl-cal-loc">' + (r.location || '') + '</div></div>' +
          (r.overall_score ? '<span class="rl-cal-score">' + r.overall_score + '</span>' : '') +
        '</div>';
      });
      html += '</div>';
    }
    if (!html) html = noResultsHtml();
    calContainer.setAttribute('role', 'region');
    calContainer.setAttribute('aria-label', 'Race calendar by month');
    calContainer.innerHTML = html;
    // Scroll to current month
    var curEl = document.getElementById('rl-cal-' + currentMonth.toLowerCase());
    if (curEl) curEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function toggleView(mode) {
    viewMode = mode;
    document.querySelectorAll('.rl-view-btn').forEach(function(b) {
      b.classList.toggle('active', b.dataset.view === mode);
    });
    var mapContainer = document.getElementById('rl-map-container');
    var tierContainer = document.getElementById('rl-tier-container');
    var calContainer = document.getElementById('rl-calendar-container');
    mapContainer.classList.remove('visible');
    tierContainer.style.display = 'none';
    if (calContainer) calContainer.style.display = 'none';
    if (mode === 'map') {
      mapContainer.classList.add('visible');
      loadLeaflet(function() {
        initMap();
        updateMapMarkers();
        setTimeout(function() { mapInstance.invalidateSize(); }, 100);
      });
    } else if (mode === 'calendar') {
      if (calContainer) { calContainer.style.display = ''; renderCalendar(); }
    } else {
      tierContainer.style.display = '';
    }
  }
  window.toggleView = toggleView;

  // ── URL state ──
  function loadFromURL() {
    var params = new URLSearchParams(window.location.search);
    if (params.get('q')) document.getElementById('rl-search').value = params.get('q');
    if (params.get('tier')) document.getElementById('rl-tier').value = params.get('tier');
    if (params.get('region')) document.getElementById('rl-region').value = params.get('region');
    if (params.get('distance')) document.getElementById('rl-distance').value = params.get('distance');
    if (params.get('month')) document.getElementById('rl-month').value = params.get('month');
    if (params.has('discipline')) document.getElementById('rl-discipline').value = params.get('discipline');
    if (params.get('sort')) currentSort = params.get('sort');

    // Restore display mode from URL
    if (params.get('display') === 'tiers') {
      displayMode = 'tiers';
    }

    // Restore match mode from URL
    if (params.get('match') === '1') {
      SLIDERS.forEach(function(s) {
        var val = params.get('q_' + s.key);
        if (val) document.getElementById('rl-q-' + s.key).value = val;
      });
      displayMode = 'match';
      document.getElementById('rl-btn-reset').style.display = '';
      var p = parseInt(params.get('page'));
      if (p > 1) matchVisibleCount = p * TIER_PAGE_SIZE;
    }

    // Restore near me from URL (triggers geolocation)
    if (params.get('nearme') === '1') {
      var r = parseInt(params.get('radius'));
      if (r) nearMeRadius = r;
      // Auto-trigger geolocation
      setTimeout(function() { activateNearMe(); }, 100);
    }

    // Restore favorites filter from URL
    if (params.get('favs') === '1') showFavoritesOnly = true;

    // Restore compare state from URL
    var cmpParam = params.get('compare');
    if (cmpParam) compareSlugs = cmpParam.split(',').filter(Boolean);
    if (params.get('cmp') === '1' && compareSlugs.length >= 2) compareMode = true;

    // Restore view mode from URL
    var urlView = params.get('view');
    if (urlView === 'map' || urlView === 'calendar') {
      setTimeout(function() { toggleView(urlView); }, 150);
    }
  }

  function saveToURL() {
    var f = getFilters();
    var params = new URLSearchParams();
    if (f.search) params.set('q', f.search);
    if (f.tier) params.set('tier', f.tier);
    if (f.region) params.set('region', f.region);
    if (f.distance) params.set('distance', f.distance);
    if (f.month) params.set('month', f.month);
    if (f.discipline !== 'gran_fondo') params.set('discipline', f.discipline);
    if (currentSort !== 'score') params.set('sort', currentSort);

    if (displayMode === 'match') {
      params.set('match', '1');
      SLIDERS.forEach(function(s) {
        var val = document.getElementById('rl-q-' + s.key).value;
        if (val !== '3') params.set('q_' + s.key, val);
      });
      if (matchVisibleCount > TIER_PAGE_SIZE) {
        params.set('page', Math.ceil(matchVisibleCount / TIER_PAGE_SIZE));
      }
    }

    if (userLat !== null) {
      params.set('nearme', '1');
      if (nearMeRadius && nearMeRadius !== 500) params.set('radius', nearMeRadius);
    }

    if (displayMode === 'tiers') params.set('display', 'tiers');
    if (showFavoritesOnly) params.set('favs', '1');
    if (viewMode && viewMode !== 'list') params.set('view', viewMode);

    if (compareSlugs.length > 0) params.set('compare', compareSlugs.join(','));
    if (compareMode) params.set('cmp', '1');

    var newURL = params.toString()
      ? window.location.pathname + '?' + params.toString()
      : window.location.pathname;
    window.history.replaceState({}, '', newURL);
  }

  // ── Filter helpers ──
  function countByFilter(filterKey, filterValue) {
    return allRaces.filter(function(r) {
      if (filterKey === 'tier') return r.tier == filterValue;
      if (filterKey === 'region') return r.region === filterValue;
      if (filterKey === 'month') return r.month === filterValue;
      if (filterKey === 'distance') {
        var parts = filterValue.split('-').map(Number);
        var d = r.distance_mi || 0;
        return d >= parts[0] && d <= parts[1];
      }
      if (filterKey === 'discipline') return (r.discipline || 'gran_fondo') === filterValue;
      return true;
    }).length;
  }

  function populateFilterOptions() {
    var tierSel = document.getElementById('rl-tier');
    tierSel.innerHTML = '<option value="">All Tiers</option>';
    [1, 2, 3, 4].forEach(function(t) {
      var count = countByFilter('tier', t);
      var opt = document.createElement('option');
      opt.value = t; opt.textContent = 'Tier ' + t + ' (' + count + ')';
      tierSel.appendChild(opt);
    });

    var regions = [];
    var seen = {};
    allRaces.forEach(function(r) {
      if (r.region && !seen[r.region]) { seen[r.region] = true; regions.push(r.region); }
    });
    regions.sort();
    var regionSel = document.getElementById('rl-region');
    regionSel.innerHTML = '<option value="">All Regions</option>';
    // Add "International" meta-region (all non-US regions)
    var intlCount = allRaces.filter(function(r) { return r.region && !US_REGIONS.has(r.region); }).length;
    if (intlCount > 0) {
      var intlOpt = document.createElement('option');
      intlOpt.value = 'International'; intlOpt.textContent = 'International (' + intlCount + ')';
      regionSel.appendChild(intlOpt);
    }
    regions.forEach(function(r) {
      var count = countByFilter('region', r);
      var opt = document.createElement('option');
      opt.value = r; opt.textContent = r + ' (' + count + ')';
      regionSel.appendChild(opt);
    });

    var distSel = document.getElementById('rl-distance');
    distSel.innerHTML = '<option value="">Any Distance</option>';
    [['0-50', 'Under 50 mi'], ['50-100', '50-100 mi'], ['100-200', '100-200 mi'], ['200-999', '200+ mi']].forEach(function(pair) {
      var count = countByFilter('distance', pair[0]);
      var opt = document.createElement('option');
      opt.value = pair[0]; opt.textContent = pair[1] + ' (' + count + ')';
      distSel.appendChild(opt);
    });

    var months = ['January','February','March','April','May','June',
                  'July','August','September','October','November','December'];
    var monthSel = document.getElementById('rl-month');
    monthSel.innerHTML = '<option value="">Any Month</option>';
    months.forEach(function(m) {
      var count = countByFilter('month', m);
      if (count > 0) {
        var opt = document.createElement('option');
        opt.value = m; opt.textContent = m + ' (' + count + ')';
        monthSel.appendChild(opt);
      }
    });

    var discSel = document.getElementById('rl-discipline');
    var currentDisc = discSel.value;
    discSel.innerHTML = '<option value="">All Types</option>';
    [['gran_fondo', 'Gran Fondo'], ['sportive', 'Sportive'], ['century', 'Century'], ['multi_stage', 'Multi-Stage'], ['hillclimb', 'Hillclimb']].forEach(function(pair) {
      var count = countByFilter('discipline', pair[0]);
      if (count > 0) {
        var opt = document.createElement('option');
        opt.value = pair[0]; opt.textContent = pair[1] + ' (' + count + ')';
        discSel.appendChild(opt);
      }
    });
    discSel.value = currentDisc || 'gran_fondo';
  }

  function getFilters() {
    var search = document.getElementById('rl-search').value.toLowerCase();
    var tier = document.getElementById('rl-tier').value;
    var region = document.getElementById('rl-region').value;
    var distance = document.getElementById('rl-distance').value;
    var month = document.getElementById('rl-month').value;
    var discipline = document.getElementById('rl-discipline').value;
    return { search: search, tier: tier, region: region, distance: distance, month: month, discipline: discipline };
  }

  function escHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function getTranscriptSnippet(searchText, query) {
    if (!searchText || !query) return '';
    var lower = searchText.toLowerCase();
    var idx = lower.indexOf(query);
    if (idx === -1) return '';
    var start = Math.max(0, idx - 50);
    var end = Math.min(searchText.length, idx + query.length + 70);
    var snippet = (start > 0 ? '...' : '') +
      escHtml(searchText.substring(start, idx)) +
      '<mark>' + escHtml(searchText.substring(idx, idx + query.length)) + '</mark>' +
      escHtml(searchText.substring(idx + query.length, end)) +
      (end < searchText.length ? '...' : '');
    return snippet;
  }

  function filterRaces() {
    var f = getFilters();
    // Clear snippet flags on ALL races upfront — prevents stale flags on races
    // that were filtered out by tier/region/distance before the reset path ran
    for (var i = 0; i < allRaces.length; i++) {
      allRaces[i]._transcriptMatch = false;
      allRaces[i]._searchQuery = '';
    }
    return allRaces.filter(function(r) {
      if (f.search) {
        var nameMatch = r.name.toLowerCase().includes(f.search);
        var locMatch = (r.location || '').toLowerCase().includes(f.search);
        var stMatch = (r.st || '').toLowerCase().includes(f.search);
        if (!nameMatch && !locMatch && !stMatch) return false;
        // Tag transcript-only matches for snippet display
        r._transcriptMatch = !nameMatch && !locMatch && stMatch;
        r._searchQuery = f.search;
      }
      if (f.tier && r.tier != f.tier) return false;
      if (f.region === 'International' && (!r.region || US_REGIONS.has(r.region))) return false;
      if (f.region && f.region !== 'International' && r.region !== f.region) return false;
      if (f.month && r.month !== f.month) return false;
      if (f.discipline && (r.discipline || 'gran_fondo') !== f.discipline) return false;
      if (f.distance) {
        var parts = f.distance.split('-').map(Number);
        var d = r.distance_mi || 0;
        if (d < parts[0] || d > parts[1]) return false;
      }
      // Near Me radius filter
      if (userLat !== null && nearMeRadius > 0) {
        var dist = raceDistances[r.slug];
        if (dist === undefined || dist > nearMeRadius) return false;
      }
      // Favorites filter
      if (showFavoritesOnly && favorites.indexOf(r.slug) === -1) return false;
      return true;
    });
  }

  function sortRaces(races) {
    var sorted = races.slice();
    switch(currentSort) {
      case 'score':
        sorted.sort(function(a, b) { return (b.overall_score || 0) - (a.overall_score || 0); });
        break;
      case 'name':
        sorted.sort(function(a, b) { return a.name.localeCompare(b.name); });
        break;
      case 'distance':
        sorted.sort(function(a, b) { return (b.distance_mi || 0) - (a.distance_mi || 0); });
        break;
      case 'nearby':
        sorted.sort(function(a, b) { return (raceDistances[a.slug] || 99999) - (raceDistances[b.slug] || 99999); });
        break;
    }
    return sorted;
  }

  // ── Score / rendering helpers ──
  function scoreColor(score) {
    if (score >= 85) return '#0d1117';
    if (score >= 75) return '#1a1a2e';
    if (score >= 65) return '#3d5a80';
    return '#6c757d';
  }

  var SCORE_LABELS = {
    distance: 'Distance', climbing: 'Climbing', descent_technicality: 'Descent Tech',
    road_surface: 'Road Surface', climate_risk: 'Climate Risk', altitude: 'Altitude',
    logistics: 'Logistics', prestige: 'Prestige', organization: 'Organization',
    scenic_experience: 'Scenic Experience', community_culture: 'Community', field_depth: 'Field Depth',
    value: 'Value', expenses: 'Expenses', cultural_impact: 'Cultural Impact'
  };

  function renderScoreBreakdown(scores) {
    if (!scores || Object.keys(scores).length < 7) return '';
    var rows = Object.entries(SCORE_LABELS).filter(function(pair) {
      var key = pair[0];
      // Only show cultural_impact if the race has it
      if (key === 'cultural_impact') return scores[key] != null && scores[key] > 0;
      return true;
    }).map(function(pair) {
      var key = pair[0], label = pair[1];
      var val = scores[key] || 0;
      var dots = Array.from({length: 5}, function(_, i) {
        return '<span class="rl-score-dot' + (i < val ? ' filled' : '') + '"></span>';
      }).join('');
      return '<div class="rl-score-row"><span class="rl-score-row-label">' + label + '</span><span class="rl-score-row-dots">' + dots + '</span></div>';
    }).join('');
    return '<div class="rl-score-breakdown"><div class="rl-score-grid">' + rows + '</div></div>';
  }

  function radarPoints(scores, vars, cx, cy, r) {
    var n = vars.length;
    return vars.map(function(v, i) {
      var val = (scores[v] || 1) / 5;
      var angle = (Math.PI * 2 * i / n) - Math.PI / 2;
      return [cx + r * val * Math.cos(angle), cy + r * val * Math.sin(angle)];
    });
  }

  function renderMiniRadar(scores) {
    if (!scores || Object.keys(scores).length < 7) return '';
    var vars = ['distance','climbing','descent_technicality','road_surface','climate_risk','altitude','logistics'];
    var cx = 40, cy = 40, r = 30;
    var n = vars.length;
    var points = radarPoints(scores, vars, cx, cy, r);
    var poly = points.map(function(p) { return p.join(','); }).join(' ');
    var grid = [0.2, 0.4, 0.6, 0.8, 1.0].map(function(s) {
      var gp = Array.from({length: n}, function(_, i) {
        var angle = (Math.PI * 2 * i / n) - Math.PI / 2;
        return [cx + r * s * Math.cos(angle), cy + r * s * Math.sin(angle)];
      });
      return '<polygon points="' + gp.map(function(p){return p.join(',');}).join(' ') + '" fill="none" stroke="#d1dce6" stroke-width="0.5"/>';
    }).join('');
    return '<svg class="rl-radar" width="80" height="80" viewBox="0 0 80 80">' +
      grid +
      '<polygon points="' + poly + '" fill="rgba(230,57,70,0.12)" stroke="#1a1a2e" stroke-width="1.5"/>' +
    '</svg>';
  }

  // Elite seal SVG — "Certified Fresh" equivalent for Tier 1 races
  var ELITE_SEAL = '<svg class="rl-elite-seal" width="28" height="28" viewBox="0 0 28 28" xmlns="http://www.w3.org/2000/svg">' +
    '<polygon points="14,1 17.5,9.5 27,10 20,16.5 22,26 14,21 6,26 8,16.5 1,10 10.5,9.5" fill="#e63946" stroke="#1a1a2e" stroke-width="1"/>' +
    '<text x="14" y="17" text-anchor="middle" font-family="Sometype Mono,monospace" font-size="7" font-weight="700" fill="#fff">RL</text>' +
  '</svg>';

  // Terrain tag based on dominant race characteristic
  function getTerrainTag(race) {
    if (!race.scores) return '';
    var s = race.scores;
    var tags = [];
    if (s.descent_technicality >= 4) tags.push('TECHNICAL');
    else if (s.descent_technicality >= 3) tags.push('MIXED');
    if (s.climbing >= 4) tags.push('CLIMBING');
    if (s.logistics >= 4) tags.push('REMOTE');
    if (s.distance >= 4) tags.push('ULTRA');
    if (tags.length === 0) {
      if (s.descent_technicality <= 2) tags.push('SMOOTH');
      else tags.push('ROAD');
    }
    return tags.slice(0, 2).map(function(t) {
      return '<span class="rl-terrain-tag">' + t + '</span>';
    }).join('');
  }

  function renderCard(race) {
    var nameTag = race.has_profile
      ? '<a class="rl-card-name" href="' + escHtml(race.profile_url) + '">' + escHtml(race.name) + '</a>'
      : '<span class="rl-card-name no-link">' + escHtml(race.name) + '</span>';

    var breakdown = renderScoreBreakdown(race.scores);

    // Score hero — prominent score number with bar below
    var scoreHero = '';
    if (race.overall_score) {
      scoreHero = '<div class="rl-card-score-hero">' +
        '<span class="rl-card-score-big" style="color:' + scoreColor(race.overall_score) + '">' + race.overall_score + '</span>' +
        '<span class="rl-card-score-label">GG</span>' +
      '</div>';
    }

    var scoreBar = race.overall_score
      ? '<div class="rl-score-bar" onclick="this.nextElementSibling&&this.nextElementSibling.classList.toggle(\'open\')" title="Click for score breakdown">' +
          '<div class="rl-score-track">' +
            '<div class="rl-score-fill" style="width:' + race.overall_score + '%;background:' + scoreColor(race.overall_score) + '"></div>' +
          '</div>' +
        '</div>' + breakdown
      : '';

    var radar = renderMiniRadar(race.scores);

    var racerBadge = '';
    if (race.racer_pct !== undefined && race.racer_pct !== null) {
      racerBadge = '<div class="rl-racer-compact">' +
        '<span class="rl-racer-compact-label">RACERS</span>' +
        '<span class="rl-racer-compact-pct">' + race.racer_pct + '%</span>' +
        '<span class="rl-racer-compact-count">' + race.racer_count + ' ratings</span>' +
      '</div>';
    } else if (race.racer_count > 0) {
      racerBadge = '<div class="rl-racer-compact rl-racer-compact--pending">' +
        '<span class="rl-racer-compact-label">RACERS</span>' +
        '<span class="rl-racer-compact-pct">&mdash;</span>' +
        '<span class="rl-racer-compact-count">' + race.racer_count + '/3 needed</span>' +
      '</div>';
    }

    var matchBadge = (displayMode === 'match' && matchScores[race.slug] !== undefined)
      ? '<span class="rl-match-badge">' + matchScores[race.slug] + '% match</span>'
      : '';

    var distBadge = '';
    if (userLat !== null && raceDistances[race.slug] !== undefined) {
      distBadge = '<span class="rl-distance-badge">' + raceDistances[race.slug].toLocaleString() + ' mi away</span>';
    }

    var compareCheck = '<label class="rl-compare-check" title="Add to compare">' +
      '<input type="checkbox" data-slug="' + escHtml(race.slug) + '"' +
        (compareSlugs.indexOf(race.slug) !== -1 ? ' checked' : '') + '>' +
      '<span class="rl-compare-check-box"></span>' +
    '</label>';

    var isFav = favorites.indexOf(race.slug) !== -1;
    var favBtn = '<button class="rl-fav-btn' + (isFav ? ' rl-fav-active' : '') + '" data-slug="' + escHtml(race.slug) + '" title="Favorite">' +
      '<span class="rl-fav-icon">' + (isFav ? '&#9829;' : '&#9825;') + '</span>' +
    '</button>';

    var discBadge = '';
    var disc = race.discipline || 'gran_fondo';
    if (disc !== 'gran_fondo') {
      var discLabelMap = { sportive: 'Sportive', century: 'Century', multi_stage: 'Multi-Stage', hillclimb: 'Hillclimb' };
      var discLabel = discLabelMap[disc] || disc.charAt(0).toUpperCase() + disc.slice(1);
      discBadge = '<span class="rl-discipline-badge">' + discLabel + '</span>';
    }

    var seriesBadge = '';
    if (race.series_name) {
      seriesBadge = '<a href="/race/series/' + escHtml(race.series_id) + '/" class="rl-series-badge">' + escHtml(race.series_name) + '</a>';
    }

    // Elite seal for Tier 1
    var eliteSeal = race.tier === 1 ? ELITE_SEAL : '';

    // Terrain tags
    var terrainTags = getTerrainTag(race);

    return '<div class="rl-card rl-card-tier-' + race.tier + '">' +
      '<div class="rl-card-header">' +
        compareCheck +
        favBtn +
        nameTag +
        '<div style="display:flex;gap:6px;align-items:center">' +
          matchBadge +
          distBadge +
          seriesBadge +
          discBadge +
          '<span class="rl-tier-badge rl-tier-' + race.tier + '">' + 'TIER ' + race.tier + '</span>' +
        '</div>' +
      '</div>' +
      '<div class="rl-card-score-row">' +
        scoreHero +
        eliteSeal +
        racerBadge +
      '</div>' +
      scoreBar +
      '<div class="rl-card-meta">' + escHtml(race.location || 'Location TBD') + (race.month ? ' &middot; ' + escHtml(race.month) : '') + '</div>' +
      '<div class="rl-card-stats">' +
        (race.distance_mi ? '<div class="rl-stat"><span class="rl-stat-val">' + race.distance_mi + '</span><span class="rl-stat-label">Miles</span></div>' : '') +
        (race.elevation_ft ? '<div class="rl-stat"><span class="rl-stat-val">' + Number(race.elevation_ft).toLocaleString() + '</span><span class="rl-stat-label">Ft Elev</span></div>' : '') +
        (terrainTags ? '<div class="rl-stat rl-stat-terrain">' + terrainTags + '</div>' : '') +
      '</div>' +
      radar +
      (race.tagline ? '<div class="rl-card-tagline">' + escHtml(race.tagline) + '</div>' : '') +
      (race._transcriptMatch ? '<div class="rl-card-transcript-snippet"><span class="rl-card-transcript-label">RIDERS SAY</span> ' + getTranscriptSnippet(race.st, race._searchQuery) + '</div>' : '') +
    '</div>';
  }

  // ── Tier grouping ──
  function groupByTier(races) {
    var groups = { 1: [], 2: [], 3: [], 4: [] };
    races.forEach(function(r) {
      var t = r.tier || 4;
      if (groups[t]) groups[t].push(r);
    });
    return groups;
  }

  function renderTierSections(filtered) {
    var groups = groupByTier(filtered);
    var container = document.getElementById('rl-tier-container');
    var totalVisible = 0;
    [1, 2, 3, 4].forEach(function(t) {
      totalVisible += Math.min(groups[t].length, tierVisibleCounts[t]);
    });
    var html = '<div class="rl-results-count">Showing ' + totalVisible + ' of ' + filtered.length + ' races</div>';

    [1, 2, 3, 4].forEach(function(t) {
      var races = groups[t];
      if (races.length === 0) return;

      var collapsed = tierCollapsed[t];
      var visible = races.slice(0, tierVisibleCounts[t]);
      var remaining = races.length - visible.length;

      html += '<div class="rl-tier-section">' +
        '<button class="rl-tier-section-header tier-' + t + '" onclick="toggleTier(' + t + ')" aria-expanded="' + (!collapsed) + '" aria-controls="rl-tier-body-' + t + '">' +
          '<div class="rl-tier-section-title">' +
            '<span class="rl-tier-badge rl-tier-' + t + '">TIER ' + t + '</span>' +
            '<h3><a href="/race/tier-' + t + '/" onclick="event.stopPropagation()" class="rl-tier-name-link">' + TIER_NAMES[t] + '</a></h3>' +
            '<span class="rl-tier-section-count">' + races.length + ' race' + (races.length !== 1 ? 's' : '') + '</span>' +
          '</div>' +
          '<p class="rl-tier-section-desc">' + TIER_DESCS[t] + '</p>' +
          '<span class="rl-tier-section-chevron' + (collapsed ? ' collapsed' : '') + '">▾</span>' +
        '</button>' +
        '<div class="rl-tier-section-body' + (collapsed ? ' collapsed' : '') + '" id="rl-tier-body-' + t + '">' +
          '<div class="rl-grid">' + visible.map(renderCard).join('') + '</div>' +
          (remaining > 0 ? '<button class="rl-load-more" onclick="loadMoreTier(' + t + ')">Show ' + Math.min(remaining, TIER_PAGE_SIZE) + ' more of ' + remaining + ' remaining</button>' : '') +
        '</div>' +
      '</div>';
    });

    if (!html) {
      html = noResultsHtml();
    }
    container.innerHTML = html;
  }

  function renderMatchResults(filtered) {
    var sorted = filtered.slice().sort(function(a, b) { return (matchScores[b.slug] || 0) - (matchScores[a.slug] || 0); });
    var container = document.getElementById('rl-tier-container');
    var visible = sorted.slice(0, matchVisibleCount);
    var remaining = sorted.length - visible.length;

    var html = '<div class="rl-match-banner">' +
      '<span>Showing results ranked by match score</span>' +
      '<button onclick="resetMatch()">Back to All Races</button>' +
    '</div>';

    if (visible.length > 0) {
      html += '<div class="rl-results-count">Showing ' + visible.length + ' of ' + sorted.length + ' races</div>';
      html += '<div class="rl-grid">' + visible.map(renderCard).join('') + '</div>';
      if (remaining > 0) {
        html += '<button class="rl-load-more" onclick="loadMoreMatches()">Show ' + Math.min(remaining, TIER_PAGE_SIZE) + ' more of ' + remaining + ' remaining</button>';
      }
    } else {
      html += noResultsHtml();
    }
    container.innerHTML = html;
  }

  var streamVisibleCount = TIER_PAGE_SIZE * 2; // show 40 at a time in stream

  function renderStreamResults(filtered) {
    var container = document.getElementById('rl-tier-container');
    var visible = filtered.slice(0, streamVisibleCount);
    var remaining = filtered.length - visible.length;

    var html = '<div class="rl-results-count">Showing ' + visible.length + ' of ' + filtered.length + ' races</div>';

    if (visible.length > 0) {
      html += '<div class="rl-grid">' + visible.map(renderCard).join('') + '</div>';
      if (remaining > 0) {
        html += '<button class="rl-load-more" onclick="loadMoreStream()">Show ' + Math.min(remaining, TIER_PAGE_SIZE) + ' more of ' + remaining + ' remaining</button>';
      }
    } else {
      html += noResultsHtml();
    }
    container.innerHTML = html;
  }

  function loadMoreStream() {
    streamVisibleCount += TIER_PAGE_SIZE;
    render(false);
  }
  window.loadMoreStream = loadMoreStream;

  function toggleDisplayMode(mode) {
    displayMode = mode;
    document.querySelectorAll('.rl-display-btn').forEach(function(b) {
      b.classList.toggle('active', b.dataset.display === mode);
    });
    render(true);
  }
  window.toggleDisplayMode = toggleDisplayMode;

  function toggleTier(t) {
    tierCollapsed[t] = !tierCollapsed[t];
    render(false);
  }
  window.toggleTier = toggleTier;

  function loadMoreTier(t) {
    tierVisibleCounts[t] += TIER_PAGE_SIZE;
    render(false);
  }
  window.loadMoreTier = loadMoreTier;

  function loadMoreMatches() {
    var prevCount = matchVisibleCount;
    matchVisibleCount += TIER_PAGE_SIZE;
    render(false);
    var cards = document.querySelectorAll('#rl-tier-container .rl-card');
    if (cards[prevCount]) cards[prevCount].scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  window.loadMoreMatches = loadMoreMatches;

  // ── Active filter pills ──
  function renderActivePills() {
    var f = getFilters();
    var container = document.getElementById('rl-active-filters');
    var pills = [];

    var distLabels = { '0-50': 'Under 50 mi', '50-100': '50-100 mi', '100-200': '100-200 mi', '200-999': '200+ mi' };
    var discLabels = { gran_fondo: 'Gran Fondo', sportive: 'Sportive', century: 'Century', multi_stage: 'Multi-Stage', hillclimb: 'Hillclimb' };
    var filterLabels = {
      search: f.search ? '"' + f.search + '"' : null,
      tier: f.tier ? 'Tier ' + f.tier : null,
      region: f.region || null,
      distance: f.distance ? distLabels[f.distance] : null,
      month: f.month || null,
      discipline: f.discipline !== 'gran_fondo' ? (f.discipline ? discLabels[f.discipline] : 'All Disciplines') : null
    };

    // Add favorites pill
    if (showFavoritesOnly) {
      pills.push('<span class="rl-filter-pill">Favorites (' + favorites.length + ')<button onclick="toggleFavoritesFilter()">×</button></span>');
    }

    // Add near me pill
    if (userLat !== null) {
      pills.push('<span class="rl-filter-pill">Near Me (' + nearMeRadius + ' mi)<button onclick="activateNearMe()">×</button></span>');
    }

    Object.entries(filterLabels).forEach(function(pair) {
      var key = pair[0], label = pair[1];
      if (label) {
        var inputId = key === 'search' ? 'rl-search' : 'rl-' + key;
        var resetVal = key === 'discipline' ? 'gran_fondo' : '';
        pills.push('<span class="rl-filter-pill">' + label + '<button onclick="document.getElementById(\'' + inputId + '\').value=\'' + resetVal + '\';document.getElementById(\'' + inputId + '\').dispatchEvent(new Event(\'change\'))">×</button></span>');
      }
    });

    if (pills.length > 1) {
      pills.push('<button class="rl-clear-all" onclick="clearAllFilters()">Clear all</button>');
    }

    container.innerHTML = pills.join('');
  }

  // ── Compare functions ──
  function toggleCompare(slug, checked) {
    if (checked && compareSlugs.indexOf(slug) === -1) {
      if (compareSlugs.length >= 4) {
        updateCompareCheckboxes();
        return;
      }
      compareSlugs.push(slug);
    } else if (!checked) {
      compareSlugs = compareSlugs.filter(function(s) { return s !== slug; });
    }
    if (compareMode && compareSlugs.length < 2) {
      compareMode = false;
      render();
      return;
    }
    updateCompareBar();
    updateCompareCheckboxes();
    saveToURL();
  }
  window.toggleCompare = toggleCompare;

  function clearCompare() {
    compareSlugs = [];
    compareMode = false;
    updateCompareBar();
    render();
  }
  window.clearCompare = clearCompare;

  function showCompare() {
    if (compareSlugs.length < 2) return;
    compareMode = true;
    render();
  }
  window.showCompare = showCompare;

  function exitCompare() {
    compareMode = false;
    render();
  }
  window.exitCompare = exitCompare;

  function updateCompareBar() {
    var bar = document.getElementById('rl-compare-bar');
    var pills = document.getElementById('rl-compare-pills');
    var btn = document.getElementById('rl-btn-compare');
    if (!bar) return;
    if (compareSlugs.length === 0) {
      bar.style.display = 'none';
      return;
    }
    bar.style.display = '';
    var slugSet = {};
    allRaces.forEach(function(r) { slugSet[r.slug] = r.name; });
    pills.innerHTML = compareSlugs.map(function(slug) {
      var name = slugSet[slug] || slug;
      return '<span class="rl-filter-pill">' + escHtml(name) + '<button class="rl-compare-remove" data-slug="' + escHtml(slug) + '">\u00d7</button></span>';
    }).join('');
    btn.disabled = compareSlugs.length < 2;
    btn.textContent = 'COMPARE (' + compareSlugs.length + ')';
  }

  function updateCompareCheckboxes() {
    document.querySelectorAll('#rl-race-search input[data-slug]').forEach(function(cb) {
      cb.checked = compareSlugs.indexOf(cb.dataset.slug) !== -1;
    });
  }

  // ── Compare panel ──
  function renderComparePanel() {
    var slugMap = {};
    allRaces.forEach(function(r) { slugMap[r.slug] = r; });
    var races = compareSlugs.map(function(s) { return slugMap[s]; }).filter(Boolean);
    if (races.length < 2) { compareMode = false; return; }

    var container = document.getElementById('rl-tier-container');
    var radarVars = ['distance','climbing','descent_technicality','road_surface','climate_risk','altitude','logistics'];

    // Banner
    var html = '<div class="rl-compare-banner">' +
      '<span>COMPARING ' + races.length + ' RACES</span>' +
      '<button onclick="exitCompare()">Back to Results</button>' +
    '</div>';

    // Table
    html += '<div class="rl-compare-table-wrap"><table class="rl-compare-table">';

    // Header row: race names
    html += '<thead><tr><th class="rl-compare-label-col"></th>';
    races.forEach(function(r, i) {
      html += '<th style="border-left:3px solid ' + COMPARE_COLORS[i].stroke + '">' +
        (r.has_profile ? '<a href="' + r.profile_url + '">' + r.name + '</a>' : r.name) +
      '</th>';
    });
    html += '</tr></thead><tbody>';

    // Tier row
    html += '<tr><td class="rl-compare-label-col">TIER</td>';
    races.forEach(function(r) {
      html += '<td><span class="rl-tier-badge rl-tier-' + r.tier + '">TIER ' + r.tier + '</span> ' + TIER_NAMES[r.tier] + '</td>';
    });
    html += '</tr>';

    // Score row with best highlight
    var scores = races.map(function(r) { return r.overall_score || 0; });
    var maxScore = Math.max.apply(null, scores);
    html += '<tr><td class="rl-compare-label-col">SCORE</td>';
    races.forEach(function(r) {
      var s = r.overall_score || 0;
      var best = s === maxScore && maxScore > 0 ? ' rl-compare-best' : '';
      html += '<td class="' + best + '"><span class="rl-compare-score-num">' + s + '</span>' +
        '<div class="rl-score-track"><div class="rl-score-fill" style="width:' + s + '%;background:' + scoreColor(s) + '"></div></div></td>';
    });
    html += '</tr>';

    // Vitals section header
    html += '<tr class="rl-compare-section-row"><td colspan="' + (races.length + 1) + '">VITALS</td></tr>';

    // Location
    html += '<tr><td class="rl-compare-label-col">LOCATION</td>';
    races.forEach(function(r) { html += '<td>' + (r.location || 'TBD') + '</td>'; });
    html += '</tr>';

    // Month
    html += '<tr><td class="rl-compare-label-col">MONTH</td>';
    races.forEach(function(r) { html += '<td>' + (r.month || 'TBD') + '</td>'; });
    html += '</tr>';

    // Distance (best = longest)
    var dists = races.map(function(r) { return r.distance_mi || 0; });
    var maxDist = Math.max.apply(null, dists);
    html += '<tr><td class="rl-compare-label-col">DISTANCE</td>';
    races.forEach(function(r) {
      var d = r.distance_mi || 0;
      var best = d === maxDist && maxDist > 0 ? ' rl-compare-best' : '';
      html += '<td class="' + best + '">' + (d ? d + ' mi' : '\u2014') + '</td>';
    });
    html += '</tr>';

    // Elevation (best = highest)
    var elevs = races.map(function(r) { return r.elevation_ft || 0; });
    var maxElev = Math.max.apply(null, elevs);
    html += '<tr><td class="rl-compare-label-col">ELEVATION</td>';
    races.forEach(function(r) {
      var e = r.elevation_ft || 0;
      var best = e === maxElev && maxElev > 0 ? ' rl-compare-best' : '';
      html += '<td class="' + best + '">' + (e ? Number(e).toLocaleString() + ' ft' : '\u2014') + '</td>';
    });
    html += '</tr>';

    // Radar chart section
    html += '<tr class="rl-compare-section-row"><td colspan="' + (races.length + 1) + '">RADAR</td></tr>';
    html += '<tr><td colspan="' + (races.length + 1) + '" class="rl-compare-radar-cell">';

    // Overlaid radar SVG
    var rCx = 100, rCy = 100, rR = 80;
    var n = radarVars.length;
    var svgContent = '';
    // Grid rings
    [0.2, 0.4, 0.6, 0.8, 1.0].forEach(function(s) {
      var gp = Array.from({length: n}, function(_, i) {
        var angle = (Math.PI * 2 * i / n) - Math.PI / 2;
        return [rCx + rR * s * Math.cos(angle), rCy + rR * s * Math.sin(angle)];
      });
      svgContent += '<polygon points="' + gp.map(function(p){return p.join(',');}).join(' ') + '" fill="none" stroke="#d1dce6" stroke-width="0.5"/>';
    });
    // Axis lines
    Array.from({length: n}, function(_, i) {
      var angle = (Math.PI * 2 * i / n) - Math.PI / 2;
      svgContent += '<line x1="' + rCx + '" y1="' + rCy + '" x2="' + (rCx + rR * Math.cos(angle)) + '" y2="' + (rCy + rR * Math.sin(angle)) + '" stroke="#d1dce6" stroke-width="0.5"/>';
    });
    // Axis labels
    var radarLabels = ['DIST','CLIMB','DESC','SURF','CLIM','ALT','LOG'];
    Array.from({length: n}, function(_, i) {
      var angle = (Math.PI * 2 * i / n) - Math.PI / 2;
      var lx = rCx + (rR + 14) * Math.cos(angle);
      var ly = rCy + (rR + 14) * Math.sin(angle);
      svgContent += '<text x="' + lx + '" y="' + ly + '" text-anchor="middle" dominant-baseline="central" font-size="8" font-family="Sometype Mono,monospace" fill="#3d5a80">' + radarLabels[i] + '</text>';
    });
    // One polygon per race
    races.forEach(function(r, idx) {
      if (!r.scores) return;
      var pts = radarPoints(r.scores, radarVars, rCx, rCy, rR);
      var poly = pts.map(function(p) { return p.join(','); }).join(' ');
      var c = COMPARE_COLORS[idx];
      svgContent += '<polygon points="' + poly + '" fill="' + c.fill + '" stroke="' + c.stroke + '" stroke-width="2"/>';
    });
    html += '<svg class="rl-compare-radar" width="200" height="200" viewBox="0 0 200 200">' + svgContent + '</svg>';

    // Legend
    html += '<div class="rl-compare-legend">';
    races.forEach(function(r, idx) {
      html += '<span class="rl-compare-legend-item"><span class="rl-compare-legend-swatch" style="background:' + COMPARE_COLORS[idx].stroke + '"></span>' + r.name + '</span>';
    });
    html += '</div>';
    html += '</td></tr>';

    // Scores section header
    html += '<tr class="rl-compare-section-row"><td colspan="' + (races.length + 1) + '">SCORES</td></tr>';

    // Score dimension rows (14 base + cultural_impact bonus if any race has it)
    Object.entries(SCORE_LABELS).filter(function(pair) {
      if (pair[0] === 'cultural_impact') return races.some(function(r) { return r.scores && r.scores.cultural_impact > 0; });
      return true;
    }).forEach(function(pair) {
      var key = pair[0], label = pair[1];
      var vals = races.map(function(r) { return (r.scores && r.scores[key]) || 0; });
      var maxVal = Math.max.apply(null, vals);
      html += '<tr><td class="rl-compare-label-col">' + label.toUpperCase() + '</td>';
      races.forEach(function(r, idx) {
        var v = (r.scores && r.scores[key]) || 0;
        var best = v === maxVal && maxVal > 0 ? ' rl-compare-best' : '';
        var dots = Array.from({length: 5}, function(_, i) {
          var cls = i < v ? (best ? 'rl-compare-dot-best' : 'rl-compare-dot-filled') : 'rl-compare-dot-empty';
          return '<span class="' + cls + '"></span>';
        }).join('');
        html += '<td class="' + best + '"><span class="rl-compare-dots">' + dots + '</span></td>';
      });
      html += '</tr>';
    });

    // View links row
    html += '<tr><td class="rl-compare-label-col"></td>';
    races.forEach(function(r) {
      html += '<td>' + (r.has_profile ? '<a href="' + r.profile_url + '" class="rl-compare-view-link">View Profile &rarr;</a>' : '') + '</td>';
    });
    html += '</tr>';

    html += '</tbody></table></div>';
    container.innerHTML = html;
  }

  function clearAllFilters() {
    document.getElementById('rl-search').value = '';
    document.getElementById('rl-tier').value = '';
    document.getElementById('rl-region').value = '';
    document.getElementById('rl-distance').value = '';
    document.getElementById('rl-month').value = '';
    document.getElementById('rl-discipline').value = 'gran_fondo';
    // Also clear near me
    if (userLat !== null) activateNearMe();
    showFavoritesOnly = false;
    updateFavoritesToggle();
    render();
  }
  window.clearAllFilters = clearAllFilters;

  function toggleFavorite(slug) {
    var idx = favorites.indexOf(slug);
    if (idx === -1) { favorites.push(slug); } else { favorites.splice(idx, 1); }
    saveFavorites();
    // Update heart icons in place
    document.querySelectorAll('.rl-fav-btn[data-slug="' + slug + '"]').forEach(function(btn) {
      var icon = btn.querySelector('.rl-fav-icon');
      if (favorites.indexOf(slug) !== -1) {
        icon.innerHTML = '&#9829;';
        btn.classList.add('rl-fav-active');
      } else {
        icon.innerHTML = '&#9825;';
        btn.classList.remove('rl-fav-active');
      }
    });
    updateFavoritesToggle();
    if (showFavoritesOnly) render();
  }
  window.toggleFavorite = toggleFavorite;

  function toggleFavoritesFilter() {
    showFavoritesOnly = !showFavoritesOnly;
    updateFavoritesToggle();
    clearActiveSaved();
    render();
    saveToURL();
  }
  window.toggleFavoritesFilter = toggleFavoritesFilter;

  function updateFavoritesToggle() {
    var btn = document.getElementById('rl-fav-toggle');
    if (!btn) return;
    btn.classList.toggle('active', showFavoritesOnly);
    btn.textContent = 'FAVORITES (' + favorites.length + ')';
  }

  // ── Saved filter configs ──
  function saveCurrentConfig() {
    if (savedConfigs.length >= 10) return;
    var name = prompt('Name this filter config:');
    if (!name || !name.trim()) return;
    name = name.trim().substring(0, 30);
    var f = getFilters();
    var config = {
      name: name,
      created: Date.now(),
      filters: { search: f.search, tier: f.tier, region: f.region, distance: f.distance, month: f.month, discipline: f.discipline },
      sliders: getSliderValues(),
      matchMode: displayMode === 'match',
      sort: currentSort,
      viewMode: viewMode,
      showFavoritesOnly: showFavoritesOnly,
      compareSlugs: compareSlugs.slice(),
      compareMode: compareMode
    };
    savedConfigs.push(config);
    try { localStorage.setItem('rl-saved-filters', JSON.stringify(savedConfigs)); } catch(e) {}
    renderSavedBar();
  }
  window.saveCurrentConfig = saveCurrentConfig;

  function loadSavedConfig(index) {
    var config = savedConfigs[index];
    if (!config) return;
    // Set filter dropdowns
    var f = config.filters || {};
    document.getElementById('rl-search').value = f.search || '';
    document.getElementById('rl-tier').value = f.tier || '';
    document.getElementById('rl-region').value = f.region || '';
    document.getElementById('rl-distance').value = f.distance || '';
    document.getElementById('rl-month').value = f.month || '';
    document.getElementById('rl-discipline').value = f.discipline || 'gran_fondo';
    // Restore sort
    if (config.sort) {
      currentSort = config.sort;
      updateSortButtons();
    }
    // Restore view mode
    if (config.viewMode && config.viewMode !== viewMode) {
      toggleView(config.viewMode);
    }
    // Restore favorites
    if (config.showFavoritesOnly !== undefined) {
      showFavoritesOnly = config.showFavoritesOnly;
      updateFavoritesToggle();
    }
    // Restore compare state
    if (config.compareSlugs) {
      compareSlugs = config.compareSlugs.slice();
      compareMode = !!config.compareMode;
      updateCompareBar();
    }
    // Handle match mode
    if (config.matchMode && config.sliders) {
      SLIDERS.forEach(function(s) {
        var el = document.getElementById('rl-q-' + s.key);
        if (el && config.sliders[s.key] !== undefined) el.value = config.sliders[s.key];
      });
      runMatch();
    } else if (displayMode === 'match') {
      resetMatch();
    } else {
      render();
      saveToURL();
    }
    // Highlight active pill
    activeSavedIndex = index;
    renderSavedBar();
  }
  window.loadSavedConfig = loadSavedConfig;

  function deleteSavedConfig(index) {
    savedConfigs.splice(index, 1);
    try { localStorage.setItem('rl-saved-filters', JSON.stringify(savedConfigs)); } catch(e) {}
    if (activeSavedIndex === index) activeSavedIndex = -1;
    else if (activeSavedIndex > index) activeSavedIndex--;
    renderSavedBar();
  }
  window.deleteSavedConfig = deleteSavedConfig;

  function renderSavedBar() {
    var bar = document.getElementById('rl-saved-bar');
    if (!bar) return;
    var atLimit = savedConfigs.length >= 10;
    var html = '<button class="rl-saved-btn"' +
      (atLimit ? ' disabled title="Maximum 10 saved configs"' : '') +
      ' onclick="saveCurrentConfig()">SAVE</button>';
    savedConfigs.forEach(function(config, i) {
      var activeClass = i === activeSavedIndex ? ' rl-saved-active' : '';
      var nameSpan = document.createElement('span');
      nameSpan.textContent = config.name;
      var escapedName = nameSpan.textContent.replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;');
      html += '<span class="rl-saved-pill' + activeClass + '" onclick="loadSavedConfig(' + i + ')">' +
        escapedName +
        '<button onclick="event.stopPropagation();deleteSavedConfig(' + i + ')">\u00d7</button>' +
      '</span>';
    });
    bar.innerHTML = html;
  }

  function clearActiveSaved() {
    if (activeSavedIndex !== -1) {
      activeSavedIndex = -1;
      renderSavedBar();
    }
  }

  // ── Main render ──
  function render(resetPages) {
    if (resetPages !== false) {
      tierVisibleCounts = { 1: TIER_PAGE_SIZE, 2: TIER_PAGE_SIZE, 3: TIER_PAGE_SIZE, 4: TIER_PAGE_SIZE };
      matchVisibleCount = TIER_PAGE_SIZE;
      streamVisibleCount = TIER_PAGE_SIZE * 2;
    }

    var filtered = sortRaces(filterRaces());

    // If match mode was loaded from URL but scores not yet computed, compute now
    if (displayMode === 'match' && Object.keys(matchScores).length === 0) {
      var vals = getSliderValues();
      allRaces.forEach(function(r) {
        matchScores[r.slug] = computeMatchScore(r, vals);
      });
    }

    document.getElementById('rl-count').textContent =
      filtered.length + ' race' + (filtered.length !== 1 ? 's' : '') + ' found';

    if (compareMode && compareSlugs.length >= 2) {
      renderComparePanel();
      renderActivePills();
      updateCompareBar();
      saveToURL();
      return;
    }

    if (displayMode === 'match') {
      renderMatchResults(filtered);
    } else if (displayMode === 'stream') {
      renderStreamResults(filtered);
    } else {
      renderTierSections(filtered);
    }

    renderActivePills();
    updateCompareCheckboxes();
    updateCompareBar();
    if (viewMode === 'map' && mapInstance) { updateMapMarkers(); }
    if (viewMode === 'calendar') { renderCalendar(); }
    saveToURL();
  }

  // ── Event binding ──
  function bindEvents() {
    var searchTimer = null;
    function debouncedRender() {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(function() { clearActiveSaved(); render(); }, 200);
    }
    // Text search: debounce to avoid DOM thrashing on every keystroke
    document.getElementById('rl-search').addEventListener('input', debouncedRender);
    // Dropdowns: render immediately on change (single event per selection)
    ['rl-tier','rl-region','rl-distance','rl-month','rl-discipline'].forEach(function(id) {
      document.getElementById(id).addEventListener('change', function() { clearActiveSaved(); render(); });
    });

    window.addEventListener('rl-reset-filters', function() {
      displayMode = 'stream';
      matchScores = {};
      matchVisibleCount = TIER_PAGE_SIZE;
      nearMeRadius = 0;
      compareSlugs = [];
      compareMode = false;
      showFavoritesOnly = false;
      tierVisibleCounts = { 1: TIER_PAGE_SIZE, 2: TIER_PAGE_SIZE, 3: TIER_PAGE_SIZE, 4: TIER_PAGE_SIZE };
      updateFavoritesToggle();
      clearActiveSaved();
      render();
    });

    document.querySelectorAll('.rl-sort-btn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        currentSort = btn.dataset.sort;
        updateSortButtons();
        clearActiveSaved();
        render();
      });
      if (btn.dataset.sort === currentSort) {
        updateSortButtons();
      }
    });
  }

  // Delegated event listeners — avoid inline onclick/onchange (XSS prevention)
  document.addEventListener('click', function(e) {
    var favBtn = e.target.closest('.rl-fav-btn');
    if (favBtn && favBtn.dataset.slug) {
      toggleFavorite(favBtn.dataset.slug);
      return;
    }
    var removeBtn = e.target.closest('.rl-compare-remove');
    if (removeBtn && removeBtn.dataset.slug) {
      toggleCompare(removeBtn.dataset.slug, false);
      return;
    }
  });
  document.addEventListener('change', function(e) {
    var cb = e.target;
    if (cb.type === 'checkbox' && cb.dataset.slug !== undefined) {
      toggleCompare(cb.dataset.slug, cb.checked);
    }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
