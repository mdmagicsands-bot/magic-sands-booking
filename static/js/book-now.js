(function () {
  const overlay = document.getElementById('ms-book-overlay');
  if (!overlay) return;

  const prebookUrl = overlay.dataset.prebookUrl || '/book/prebook/';
  const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
  const csrfToken = csrfInput ? csrfInput.value : (overlay.dataset.csrf || '');

  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? match[2] : '';
  }

  function showOverlay(message) {
    const msgEl = overlay.querySelector('.ms-book-overlay-msg');
    if (msgEl && message) msgEl.textContent = message;
    overlay.hidden = false;
  }

  function hideOverlay() {
    overlay.hidden = true;
  }

  function setProcessing(btn, on) {
    if (!btn) return;
    btn.classList.toggle('is-processing', on);
    btn.disabled = on;
    if (on) {
      btn.dataset.originalText = btn.innerHTML;
      btn.innerHTML = 'Processing…';
    } else if (btn.dataset.originalText) {
      btn.innerHTML = btn.dataset.originalText;
    }
  }

  document.addEventListener('click', function (e) {
    const btn = e.target.closest('.js-book-now');
    if (!btn) return;
    e.preventDefault();

    const offerId = btn.dataset.offerId || '';
    if (!offerId) return;

    setProcessing(btn, true);
    showOverlay('Please wait checking availability…');

    const formData = new FormData();
    formData.append('offer_id', offerId);
    formData.append('hotel_id', btn.dataset.hotelId || '');
    formData.append('hotel_name', btn.dataset.hotelName || '');
    formData.append('checkin', btn.dataset.checkin || '');
    formData.append('checkout', btn.dataset.checkout || '');
    formData.append('adults', btn.dataset.adults || '2');
    formData.append('nationality', btn.dataset.nationality || '');
    formData.append('portal', btn.dataset.portal || 'public');
    formData.append('room_name', btn.dataset.roomName || '');
    formData.append('board', btn.dataset.board || '');
    formData.append('board_type', btn.dataset.boardType || '');
    formData.append('refundable_label', btn.dataset.refundableLabel || '');
    formData.append('is_refundable', btn.dataset.isRefundable || '0');
    formData.append('currency', btn.dataset.currency || 'USD');
    formData.append('hotel_photo', btn.dataset.hotelPhoto || '');
    formData.append('hotel_stars', btn.dataset.hotelStars || '0');
    formData.append('hotel_address', btn.dataset.hotelAddress || '');
    formData.append('occupancy_label', btn.dataset.occupancyLabel || '');
    formData.append('rooms_count', btn.dataset.roomsCount || '1');
    formData.append('nights', btn.dataset.nights || '1');
    formData.append('hotel_remarks', btn.dataset.hotelRemarks || '');
    formData.append('cancel_policies', btn.dataset.cancel || '[]');

    fetch(prebookUrl, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken || getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: formData,
      credentials: 'same-origin',
    })
      .then(function (res) {
        return res.json().then(function (data) {
          return { ok: res.ok, data: data };
        });
      })
      .then(function (result) {
        hideOverlay();
        setProcessing(btn, false);
        if (result.ok && result.data.ok && result.data.redirect) {
          window.location.href = result.data.redirect;
          return;
        }
        const msg = (result.data && result.data.error) || 'This rate is no longer available. Please choose another room.';
        alert(msg);
      })
      .catch(function () {
        hideOverlay();
        setProcessing(btn, false);
        alert('Could not check availability. Please try again.');
      });
  });
})();
