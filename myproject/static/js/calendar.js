document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    
    const calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      locale: 'ko',
      height: 'auto',
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek,timeGridDay'
      },
      events: {
        url: '/api/calendar/events/', // 실제 이벤트 로딩 경로
        failure() {
          alert('이벤트 로딩에 실패했습니다.');
        }
      },
      eventContent: function(info) {
        const eventType = info.event.extendedProps.kind;
        const eventDate = info.event.startStr;  // 이벤트 시작 날짜
        
        // 같은 날짜와 종류의 일정은 한 번만 표시하도록 처리
        const eventsOnSameDay = calendar.getEvents().filter(event => 
          event.startStr === eventDate && event.extendedProps.kind === eventType
        );
        
        // 첫 번째 일정만 표시하고 그 이후 일정은 숨김
        if (eventsOnSameDay.indexOf(info.event) > 0) {
          info.el.style.display = 'none';  // 두 번째 이후 일정은 숨기기
        }

        // 일정 종류만 표시하고 기본 제목을 숨깁니다.
        const customHtml = `<div class="event-kind">${eventType}</div>`;
        return { html: customHtml };  // 이벤트에 일정 종류만 표시
      },
      // 클릭한 이벤트에 대한 세부 정보 표시
      eventClick: function(info) {
        const eventType = info.event.extendedProps.kind;
        const eventDate = info.event.startStr;

        // 동일한 날짜와 종류를 가진 모든 일정들을 필터링
        const relatedEvents = calendar.getEvents().filter(event => 
          event.startStr === eventDate && event.extendedProps.kind === eventType
        );
        
        // 해당 종류의 일정들을 모달에 표시
        let content = `<h3>${eventType}</h3><ul>`;
        relatedEvents.forEach(event => {
          content += `<li>${event.title} (${event.startStr})</li>`;
        });
        content += '</ul>';
        
        // 세부 내용 팝업 모달에 동적으로 삽입
        document.querySelector('#eventDetailModal .modal-body').innerHTML = content;
        $('#eventDetailModal').modal('show');  // 모달 띄우기
      },
      dayMaxEvents: 5,  // 하루 최대 표시할 이벤트 수
      moreLinkText: function(n) {
        return `+${n}개 더보기`;
      }
    });
    
    calendar.render();
});
