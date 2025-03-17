let event_location = document.querySelector('#event_location')
let options = event_location.options
var event_locations_dict = {}

for (let i = 0; i < options.length; i++) {
	event_locations_dict[options[i].value] = options[i].text
}

function sortEvents(eventarray) {
	let events = [];
	for (let i = 0; i < eventarray.length; i++) {
		if (eventarray[i] == null) {
			continue
		}
		
		events.push({ 'obj': eventarray[i], 'date': new Date(eventarray[i].start_time) });
	};
	const sortByDate = (a, b) => {
		return a.date - b.date;
	};
	

	events.sort(sortByDate)
	eventarray = []
	for (let i = 0; i < events.length; i++) {
		eventarray.push(events[i].obj)

	}
	return (eventarray);
}

function clearModal() {
	document.querySelector('#event_start_time').value = "";
	document.querySelector('#event_end_time').value = "";
	document.querySelector('#event_location').value = "";
	document.querySelector('#modal_event_id').value = "";
	document.querySelector('#modal_event_pk').value = "";
}

function setEventId() {
	let trainingseventid = document.querySelector('#modal_event_id').value


	if (document.querySelector('#event_start_time').value &&
		document.querySelector('#event_end_time').value &&
		document.querySelector('#modal_event_pk').value &&
		document.querySelector('#event_location').value
	) {
		if (trainingseventid == 'new') {
			events_global.push({});
			trainingseventid = events_global.length
			trainingseventid = trainingseventid - 1
		}
		
		let trainingsevent = events_global[trainingseventid]


		trainingsevent.start_time = document.querySelector('#event_start_time').value
		trainingsevent.id = document.querySelector('#modal_event_pk').value
		trainingsevent.end_time = document.querySelector('#event_end_time').value;
		trainingsevent.location_id = document.querySelector('#event_location').value;
		trainingsevent.location = event_locations_dict[trainingsevent.location_id]
		console.log(trainingsevent)
	} else {
		return false;
	}

	return (true)
}

function setActionButtonEvents (){
	var eveltmodel_element = document.querySelector('#eventModal')	

	jQuery('.delete_event_button').on('click', function(event) {
		event_id = event.currentTarget.getAttribute('data-bs-eventid');
		if (event_id != null) {
			delete events_global[event_id];
			render_event_table();
		}
		});
		
	jQuery('.saveevent').on('click', function(event) {
		let eventmodal = bootstrap.Modal.getOrCreateInstance(eveltmodel_element) // Returns a Bootstrap modal instance
		
		if (setEventId()) {
			render_event_table();
			clearModal();
			eventmodal.hide();
		}
	});

	jQuery('.add_event_button').on('click', function(event) {
		let eventmodal = bootstrap.Modal.getOrCreateInstance(eveltmodel_element) // Returns a Bootstrap modal instance
		
		document.querySelector('#modal_event_id').value = "new";
		document.querySelector('#modal_event_pk').value = "new";

		eventmodal.show()
		
	});
}

function render_event_table() {
	var table_data = document.getElementById("EventsTable");

	events_global = sortEvents(events_global);

	let html = ""
	let table_header = `
	<thead id="table_header">
		<tr class="">
			<th class="list-checkbox-column ps-1 pe-1">
			<button type="button" class="btn p-0 add_event_button"><i class="bi bi-plus-square-fill"></i></button>

			</th>
			<th class="list-checkbox-column ps-1 pe-1"></th>
			<th class="column-header"><small>Start Time</small></th>
			<th class="column-header"><small>End Time</small></th>
			<th class="column-header"><small>Location</small></th>
		</tr>
	</thead>
	`

	for (let i = 0; i < events_global.length; i++) {
		let event = events_global[i];
		if (events_global.lenght == 0 || event == null) {
			continue
		}
		let start_time = new Date(event.start_time)
		let end_time = new Date(event.end_time)
		
		html += `
		<tr>
		<input type="hidden" id="event_id_${i}" name="event_id_${i}" value="${event.id}" />
		<input type="hidden" id="event_location_id_${i}" name="event_location_id_${i}" value="${event.location_id}" />
		<input type="hidden" id="event_start_time_${i}" name="event_start_time_${i}"" value="${event.start_time}" />
		<input type="hidden" id="event_end_time_${i}"" name="event_end_time_${i}"" value="${event.end_time}" />

		
			<td class="">
			<button type="button" class="btn p-0" data-bs-toggle="modal" data-bs-target="#eventModal" data-bs-eventid="${i}"><i class="bi bi-pencil-fill"></i></button>
			</td>
			<td class="small">
			<button type="button" class="btn p-0 delete_event_button" data-bs-eventid="${i}"><i class="bi bi-trash-fill"></i></button>
			</td>
			
			
			<td class="small">${start_time.toDateString()}, ${start_time.getHours()}:${start_time.getMinutes()}</td>
			<td class="small">${end_time.toDateString()}, ${end_time.getHours()}:${end_time.getMinutes()}</td>
			<td class="small">${event.location}</td>

		</tr>
		`
	};

	table_data.innerHTML = table_header + html

	setActionButtonEvents()
}


(() => {
	var eveltmodel_element = document.querySelector('#eventModal')

	render_event_table()

	eveltmodel_element.addEventListener('show.bs.modal', function(event) {
		let eventmodal = bootstrap.Modal.getOrCreateInstance(eveltmodel_element) // Returns a Bootstrap modal instance
		let trainingseventid
		if (event.relatedTarget) {
			trainingseventid = event.relatedTarget.getAttribute("data-bs-eventid")

			let trainingsevent = events_global[trainingseventid]

			document.querySelector('#event_start_time').value = trainingsevent.start_time;
			document.querySelector('#event_end_time').value = trainingsevent.end_time;
			document.querySelector('#event_location').value = trainingsevent.location_id;
			document.querySelector('#modal_event_id').value = trainingseventid;
			document.querySelector('#modal_event_pk').value = trainingsevent.id;

		} else {
			trainingseventid = 'new'
		}

	})

})()