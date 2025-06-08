function scaleUI() {
  const baseWidth = 2560;
  const currentWidth = window.innerWidth;
  const scale = currentWidth / baseWidth;

  const screen = document.querySelector('.screen');

  if (screen) {
    screen.style.transform = `scale(${scale})`;
    screen.style.transformOrigin = 'top left';
    screen.style.width = `${baseWidth}px`;
  }


}

function resizeFont() {
  const calendarWrapper = document.getElementById('calendar-wrapper');
  const width = window.innerWidth;

  // 예: 2560px 기준으로 폰트 크기 조절
  const baseFontSize = 16;
  const fontSize = Math.min(Math.max((width / 2560) * baseFontSize, 12), 20);

  calendarWrapper.style.fontSize = fontSize + 'px';
}


window.addEventListener('load', scaleUI, resizeFont);
window.addEventListener('resize', scaleUI, resizeFont);







document.addEventListener('DOMContentLoaded', function () {
  const calendarEl = document.getElementById('calendar');
  const renderedKindsOnDates = new Set();

  let currentFilterKind = 'all';  // 필터 기본값 (전체)
  let eventsData = []; // API에서 받아온 전체 이벤트 저장용

  const kindOrder = {
    "본회의": 1,
    "위원회": 2,
    "의장단": 3,
    "의장단(국회의장)": 3,
    "세미나": 4,
    "국회행사": 5,
    "기자회견": 6
  };

  function sortEventsByKind(events) {
    return events.slice().sort((a, b) => {
      const aKind = a.extendedProps.kind || "";
      const bKind = b.extendedProps.kind || "";

      const aOrder = kindOrder[aKind] || 99;
      const bOrder = kindOrder[bKind] || 99;

      if (aOrder !== bOrder) return aOrder - bOrder;

      return new Date(a.start) - new Date(b.start);
    });
  }

  function filterEventsByKind(events, kind) {
    if (kind === 'all') return events;
    if (kind === '의장단') {
      return events.filter(e => e.extendedProps.kind === '의장단' || e.extendedProps.kind === '의장단(국회의장)');
    }
    return events.filter(e => e.extendedProps.kind === kind);
  }

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    locale: 'ko',
    headerToolbar: false,
    events: {
      url: '/api/calendar/events/',
      failure() {
        alert('이벤트 로딩에 실패했습니다.');
      },
      success(events) {
        eventsData = events.map(event => {
          if (!event.extendedProps.committee) {
            event.extendedProps.committee = "미정";
          }
          return event;
        });
        const filtered = filterEventsByKind(eventsData, currentFilterKind);
        return sortEventsByKind(filtered);
      }
    },
    eventDidMount(info) {
      const eventType = info.event.extendedProps.kind;
      const eventDate = info.event.startStr.split('T')[0];
      const key = `${eventDate}_${eventType}`;

      if (!eventType || eventType.trim() === "") {
        info.el.style.display = 'none';
        return;
      }

      if (renderedKindsOnDates.has(key)) {
        info.el.style.display = 'none';
        return;
      }

      renderedKindsOnDates.add(key);

      const colorMap = {
        "본회의": "#2196F3",
        "위원회": "#4CAF50",
        "의장단": "#FF9800",
        "의장단(국회의장)": "#FF9800",
        "세미나": "#FFC107",
        "국회행사": "#F44336"
      };
      const color = colorMap[eventType] || "#999";

      const timeEl = info.el.querySelector('.fc-event-time');
      if (timeEl) timeEl.remove();

      const titleEl = info.el.querySelector('.fc-event-title');
      if (titleEl) {
        titleEl.textContent = '';
        const dot = document.createElement('span');
        dot.textContent = '●';
        dot.style.color = color;
        dot.style.marginRight = '4px';
        const text = document.createTextNode(eventType);
        titleEl.appendChild(dot);
        titleEl.appendChild(text);
      } else {
        const div = document.createElement('div');
        div.className = 'fc-event-title';
        const dot = document.createElement('span');
        dot.textContent = '●';
        dot.style.color = color;
        dot.style.marginRight = '4px';
        const text = document.createTextNode(eventType);
        div.appendChild(dot);
        div.appendChild(text);
        info.el.appendChild(div);
      }

      info.el.style.margin = '0';
      info.el.style.padding = '0';
      info.el.style.border = 'none';

      const titleDiv = info.el.querySelector('.fc-event-title');
      if (titleDiv) {
        titleDiv.style.margin = '0';
        titleDiv.style.padding = '0';
        titleDiv.style.lineHeight = '1.2';
      }
    },

    eventClick(info) {
      info.jsEvent.preventDefault();
    },

    dayMaxEvents: 10,
    moreLinkText(n) {
      return n === 0 ? '' : `+${n}개 더보기`;
    },

    datesSet() {
      renderedKindsOnDates.clear();

      const currentDate = calendar.getDate();
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth() + 1;

      const yearEl = document.querySelector('.text-wrapper-2');
      const monthEl = document.querySelector('.text-wrapper-3');
      if (yearEl && monthEl) {
        yearEl.textContent = `${year}년`;
        monthEl.textContent = `${month}월`;
      }

      document.querySelectorAll('.fc-daygrid-day').forEach(dayCell => {
        dayCell.style.cursor = 'pointer';
        dayCell.onclick = (e) => {
          const dateStr = dayCell.getAttribute('data-date');
          if (!dateStr) return;

          const filtered = eventsData.filter(event => {
            const isSameDate = event.start.startsWith(dateStr);
            const matchesFilter = (currentFilterKind === 'all') ||
              (event.extendedProps.kind === currentFilterKind) ||
              (currentFilterKind === '의장단' && (event.extendedProps.kind === '의장단' || event.extendedProps.kind === '의장단(국회의장)'));
            return isSameDate && matchesFilter;
          });
          showModalEvents(dateStr, sortEventsByKind(filtered));
        };
      });
    }
  });

  calendar.render();

  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      currentFilterKind = btn.getAttribute('data-kind');

      const currentDate = calendar.getDate();
      calendar.refetchEvents();
      calendar.gotoDate(currentDate);

      const detailContainer = document.querySelector('.frame-2 .modal-body');
      if (detailContainer) {
        const modalDate = detailContainer.getAttribute('data-date');
        if (modalDate) {
          const filtered = eventsData.filter(event => {
            const isSameDate = event.start.startsWith(modalDate);
            const matchesFilter = (currentFilterKind === 'all') ||
              (event.extendedProps.kind === currentFilterKind) ||
              (currentFilterKind === '의장단' && (event.extendedProps.kind === '의장단' || event.extendedProps.kind === '의장단(국회의장)'));
            return isSameDate && matchesFilter;
          });
          showModalEvents(modalDate, sortEventsByKind(filtered));
        }
      }
    });
  });

  document.querySelector('.left').addEventListener('click', function () {
    calendar.prev();
  });

  document.querySelector('.right').addEventListener('click', function () {
    calendar.next();
  });

  const scrollArea = document.querySelector('.view-4');
  let scrollbar = document.querySelector('.view-5');

  if (scrollArea) {
    if (!scrollbar) {
      scrollbar = document.createElement('div');
      scrollbar.classList.add('view-5');
      scrollArea.appendChild(scrollbar);
    }

    const handle = document.createElement('div');
    scrollbar.appendChild(handle);

    function updateHandleHeight() {
      const visibleRatio = scrollArea.clientHeight / scrollArea.scrollHeight;
      const handleHeight = Math.max(scrollArea.clientHeight * visibleRatio, 30);
      handle.style.height = handleHeight + 'px';
    }

    function updateHandlePosition() {
      const scrollRatio = scrollArea.scrollTop / (scrollArea.scrollHeight - scrollArea.clientHeight);
      const maxTop = scrollbar.clientHeight - handle.offsetHeight;
      handle.style.top = scrollRatio * maxTop + 'px';
    }

    scrollArea.addEventListener('scroll', updateHandlePosition);
    updateHandleHeight();
    updateHandlePosition();

    let isDragging = false;
    let dragStartY = 0;
    let handleStartTop = 0;

    handle.addEventListener('mousedown', (e) => {
      isDragging = true;
      dragStartY = e.clientY;
      handleStartTop = parseFloat(handle.style.top) || 0;
      e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const deltaY = e.clientY - dragStartY;
      let newTop = handleStartTop + deltaY;
      newTop = Math.max(0, Math.min(newTop, scrollbar.clientHeight - handle.offsetHeight));
      handle.style.top = newTop + 'px';

      const scrollRatio = newTop / (scrollbar.clientHeight - handle.offsetHeight);
      scrollArea.scrollTop = scrollRatio * (scrollArea.scrollHeight - scrollArea.clientHeight);
    });

    document.addEventListener('mouseup', () => {
      isDragging = false;
    });

    handle.addEventListener('touchstart', (e) => {
      isDragging = true;
      dragStartY = e.touches[0].clientY;
      handleStartTop = parseFloat(handle.style.top) || 0;
      e.preventDefault();
    });

    document.addEventListener('touchmove', (e) => {
      if (!isDragging) return;
      const deltaY = e.touches[0].clientY - dragStartY;
      let newTop = handleStartTop + deltaY;
      newTop = Math.max(0, Math.min(newTop, scrollbar.clientHeight - handle.offsetHeight));
      handle.style.top = newTop + 'px';

      const scrollRatio = newTop / (scrollbar.clientHeight - handle.offsetHeight);
      scrollArea.scrollTop = scrollRatio * (scrollArea.scrollHeight - scrollArea.clientHeight);
    });

    document.addEventListener('touchend', () => {
      isDragging = false;
    });

    window.addEventListener('resize', () => {
      updateHandleHeight();
      updateHandlePosition();
    });
  }

  function showModalEvents(dateStr, events) {
    const detailEl = document.querySelector('.frame-2 .modal-body');
    if (!detailEl) return;
    detailEl.setAttribute('data-date', dateStr);

    detailEl.innerHTML = '';

    if (events.length === 0) {
      detailEl.innerHTML = '<div class="empty-msg">해당 날짜에 일정이 없습니다.</div>';
      return;
    }

    events.forEach(event => {
      const item = document.createElement('div');
      item.className = 'modal-item';

      const time = event.start ? event.start.slice(11, 16) : '';
      const kind = event.extendedProps.kind || '';
      const title = event.title || '';
      const committee = event.extendedProps.committee || '';

      const colorMap = {
        "본회의": "#2196F3",
        "위원회": "#4CAF50",
        "의장단": "#FF9800",
        "의장단(국회의장)": "#FF9800",
        "세미나": "#FFC107",
        "국회행사": "#F44336"
      };
      const color = colorMap[kind] || "#999";

      item.innerHTML = `
        <div class="modal-item-time">${time}</div>
        <div class="modal-item-kind" style="color:${color};">● ${kind}</div>
        <div class="modal-item-title">${title}</div>
        <div class="modal-item-committee">${committee}</div>
      `;

      detailEl.appendChild(item);
    });
  }

    const menuBtn = document.getElementById('menu-button');
    const slideMenu = document.getElementById('slide-menu');

    menuBtn.addEventListener('click', function () {
      slideMenu.classList.toggle('active');
    });



});
