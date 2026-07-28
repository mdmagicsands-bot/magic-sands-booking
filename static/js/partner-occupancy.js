/**
 * Magic Sands partner Room Information (Nuitee occupancies).
 * Closed by default; opens on trigger click; Done collapses it.
 * Per room: adults 1–9, children 0–4, child ages 1–18.
 */
(function () {
  'use strict';

  function boot() {
    var btn = document.getElementById('ms-room-btn');
    var pop = document.getElementById('ms-room-pop');
    var label = document.getElementById('ms-room-label');
    var list = document.getElementById('ms-room-list');
    var addBtn = document.getElementById('ms-room-add');
    var doneBtn = document.getElementById('ms-room-done');
    var occInput = document.getElementById('occupancies');
    var adultsInput = document.getElementById('adults');
    var roomsInput = document.getElementById('rooms');
    if (!btn || !pop || !list || !occInput) return;

    var MAX_ROOMS = parseInt(pop.getAttribute('data-max-rooms') || '4', 10);
    var MAX_ADULTS = parseInt(pop.getAttribute('data-max-adults') || '9', 10);
    var MAX_CHILDREN = parseInt(pop.getAttribute('data-max-children') || '4', 10);
    var MIN_AGE = parseInt(pop.getAttribute('data-min-age') || '1', 10);
    var MAX_AGE = parseInt(pop.getAttribute('data-max-age') || '18', 10);

    var rooms = [];

    function parseRooms() {
      try {
        var raw = JSON.parse(occInput.value || '[]');
        if (Array.isArray(raw) && raw.length) {
          rooms = raw.slice(0, MAX_ROOMS).map(function (r) {
            var ages = (r.children || []).map(function (a) { return parseInt(a, 10); })
              .filter(function (a) { return a >= MIN_AGE && a <= MAX_AGE; })
              .slice(0, MAX_CHILDREN);
            return {
              adults: Math.max(1, Math.min(MAX_ADULTS, parseInt(r.adults || 2, 10) || 2)),
              children: ages,
            };
          });
        }
      } catch (e) {
        rooms = [];
      }
      if (!rooms.length) rooms = [{ adults: 2, children: [] }];
    }

    function ageSelect(selected, roomIdx, childIdx) {
      var html = '<select class="ms-age" data-r="' + roomIdx + '" data-c="' + childIdx + '">';
      for (var a = MIN_AGE; a <= MAX_AGE; a++) {
        html += '<option value="' + a + '"' + (a === selected ? ' selected' : '') + '>' + a + '</option>';
      }
      return html + '</select>';
    }

    function sync() {
      var adults = 0;
      var children = 0;
      var payload = rooms.map(function (r) {
        adults += r.adults;
        children += r.children.length;
        var o = { adults: r.adults };
        if (r.children.length) o.children = r.children.slice();
        return o;
      });
      occInput.value = JSON.stringify(payload);
      if (adultsInput) adultsInput.value = String(adults);
      if (roomsInput) roomsInput.value = String(payload.length);
      if (label) {
        var roomWord = payload.length === 1 ? 'room' : 'rooms';
        var adultWord = adults === 1 ? 'adult' : 'adults';
        var childWord = children === 1 ? 'child' : 'children';
        label.textContent = payload.length + ' ' + roomWord + ' (' + adults + ' ' + adultWord + ', ' + children + ' ' + childWord + ')';
      }
    }

    function render() {
      list.innerHTML = rooms.map(function (room, i) {
        var head = rooms.length > 1
          ? '<div class="ms-room-head"><strong>Room ' + (i + 1) + '</strong>' +
            '<button type="button" class="ms-room-remove" data-r="' + i + '">Remove</button></div>'
          : '';
        var ages = room.children.map(function (age, c) {
          return '<label class="ms-age-row">Child ' + (c + 1) + ' age ' + ageSelect(age, i, c) + '</label>';
        }).join('');
        return (
          '<div class="ms-room-card">' + head +
          '<div class="ms-row"><span>Adults</span><div class="ms-step">' +
          '<button type="button" data-r="' + i + '" data-f="adults" data-d="-1">−</button>' +
          '<b>' + room.adults + '</b>' +
          '<button type="button" data-r="' + i + '" data-f="adults" data-d="1">+</button></div></div>' +
          '<div class="ms-row"><span>Children</span><div class="ms-step">' +
          '<button type="button" data-r="' + i + '" data-f="children" data-d="-1">−</button>' +
          '<b>' + room.children.length + '</b>' +
          '<button type="button" data-r="' + i + '" data-f="children" data-d="1">+</button></div></div>' +
          (ages ? '<div class="ms-ages">' + ages + '</div>' : '') +
          '</div>'
        );
      }).join('');

      if (addBtn) addBtn.style.display = rooms.length >= MAX_ROOMS ? 'none' : '';

      list.querySelectorAll('button[data-f]').forEach(function (el) {
        el.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          var i = parseInt(el.getAttribute('data-r'), 10);
          var f = el.getAttribute('data-f');
          var d = parseInt(el.getAttribute('data-d'), 10);
          var room = rooms[i];
          if (!room) return;
          if (f === 'adults') {
            room.adults = Math.max(1, Math.min(MAX_ADULTS, room.adults + d));
          } else {
            var n = room.children.length + d;
            if (n < 0 || n > MAX_CHILDREN) return;
            if (d > 0) room.children.push(Math.min(8, MAX_AGE));
            else room.children.pop();
          }
          render();
          sync();
        });
      });

      list.querySelectorAll('.ms-room-remove').forEach(function (el) {
        el.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          var i = parseInt(el.getAttribute('data-r'), 10);
          if (rooms.length <= 1) return;
          rooms.splice(i, 1);
          render();
          sync();
        });
      });

      list.querySelectorAll('.ms-age').forEach(function (el) {
        el.addEventListener('change', function (e) {
          e.stopPropagation();
          var i = parseInt(el.getAttribute('data-r'), 10);
          var c = parseInt(el.getAttribute('data-c'), 10);
          if (rooms[i]) rooms[i].children[c] = parseInt(el.value, 10);
          sync();
        });
        el.addEventListener('click', function (e) { e.stopPropagation(); });
      });
    }

    function open() {
      render();
      pop.classList.add('is-open');
      btn.setAttribute('aria-expanded', 'true');
    }

    function close() {
      sync();
      pop.classList.remove('is-open');
      btn.setAttribute('aria-expanded', 'false');
    }

    function isOpen() {
      return pop.classList.contains('is-open');
    }

    parseRooms();
    sync();
    close();

    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (isOpen()) close();
      else open();
    });

    if (addBtn) {
      addBtn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        if (rooms.length >= MAX_ROOMS) return;
        rooms.push({ adults: 2, children: [] });
        render();
        sync();
      });
    }

    if (doneBtn) {
      doneBtn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        close();
      });
    }

    pop.addEventListener('click', function (e) { e.stopPropagation(); });
    document.addEventListener('click', function () {
      if (isOpen()) close();
    });

    var form = document.getElementById('guest-search-form');
    if (form) {
      form.addEventListener('submit', function () { sync(); });
    }

    // Expose for recent-search restore
    window.msPartnerOccupancy = {
      setRooms: function (next) {
        if (!Array.isArray(next) || !next.length) return;
        rooms = next.slice(0, MAX_ROOMS).map(function (r) {
          return {
            adults: Math.max(1, Math.min(MAX_ADULTS, parseInt(r.adults || 2, 10) || 2)),
            children: (r.children || []).map(function (a) { return parseInt(a, 10); })
              .filter(function (a) { return a >= MIN_AGE && a <= MAX_AGE; })
              .slice(0, MAX_CHILDREN),
          };
        });
        if (!rooms.length) rooms = [{ adults: 2, children: [] }];
        sync();
        close();
      },
      getRooms: function () { return rooms.slice(); },
    };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
