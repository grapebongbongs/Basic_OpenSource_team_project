document.addEventListener('DOMContentLoaded', function () {
  const calendarEl = document.getElementById('calendar');
  const renderedKindsOnDates = new Set(); // 중복 방지용 메모리

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    locale: 'ko',
    height: 'auto',
    headerToolbar: false,
    events: {
      url: '/api/calendar/events/',
      failure() {
        alert('이벤트 로딩에 실패했습니다.');
      },
      eventSourceSuccess(events) {
        return events.map(event => {
          if (!event.extendedProps.committee) {
            event.extendedProps.committee = "미정";
          }
          return event;
        });
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
        "세미나": "#FFC107",
        "국회행사": "#F44336"
      };
      const color = colorMap[eventType] || "#999";

      const timeEl = info.el.querySelector('.fc-event-time');
      if (timeEl) {
        timeEl.remove();
      }

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
      const eventType = info.event.extendedProps.kind;
      const eventDate = info.event.startStr.split('T')[0];
      const relatedEvents = calendar.getEvents().filter(event =>
        event.startStr.startsWith(eventDate) &&
        event.extendedProps.kind === eventType
      );

      let content = `<h3>${eventType}</h3><ul>`;
      relatedEvents.forEach(event => {
        content += `
          <li>
            <strong>${event.title}</strong><br/>
            장소: ${event.extendedProps.place || '장소 없음'}
          </li>`;
      });
      content += '</ul>';

      document.querySelector('#eventDetailModal .modal-body').innerHTML = content;
      $('#eventDetailModal').modal('show');
    },
    dayMaxEvents: 10,
    moreLinkText(n) {
      return n === 0 ? '' : `+${n}개 더보기`;
    },
    datesSet() {
      renderedKindsOnDates.clear();

      // 현재 날짜 기준으로 연도/월 텍스트 갱신
      const currentDate = calendar.getDate();
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth() + 1;

      const yearEl = document.querySelector('.text-wrapper-2');
      const monthEl = document.querySelector('.text-wrapper-3');
      if (yearEl && monthEl) {
        yearEl.textContent = `${year}년`;
        monthEl.textContent = `${month}월`;
      }
    }
  });

  calendar.render();

  document.querySelector('.left').addEventListener('click', function () {
    calendar.prev();
  });

  document.querySelector('.right').addEventListener('click', function () {
    calendar.next();
  });
});
