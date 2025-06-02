
function getFormattedElement(timeZone, name, value, ...dateParams) {
    return (new Intl.DateTimeFormat('en', {
        [name]: value,
        timeZone,
    }).formatToParts(new Date(...dateParams)).find(el => el.type === name) || {}).value;
}

function getTzAbbreviation(timeZone) {
    return getFormattedElement(timeZone, 'timeZoneName', "short")
}

let event_location = document.querySelector('#event_location')
let options = event_location.options
var event_locations_dict = {}

for (let i = 0; i < options.length; i++) {
	event_locations_dict[options[i].value] = options[i].text
}

function getUTCDate(date) {
    return moment(date).utc().format('YYYY-MM-DDTHH:mm:ss');
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

function setModalWithData(trainingseventid){
	let trainingsevent = events_global[trainingseventid]

	document.querySelector('#event_start_time').value = moment.utc(trainingsevent.start_time).local().format('YYYY-MM-DD HH:mm:ss');
	document.querySelector('#event_end_time').value = moment.utc(trainingsevent.end_time).local().format('YYYY-MM-DD HH:mm:ss')
	document.querySelector('#event_location').value = trainingsevent.location_id;
	document.querySelector('#modal_event_id').value = trainingseventid;
	document.querySelector('#modal_event_pk').value = trainingsevent.id;

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


		trainingsevent.start_time = getUTCDate(document.querySelector('#event_start_time').value)
		trainingsevent.id = document.querySelector('#modal_event_pk').value
		trainingsevent.end_time = getUTCDate(document.querySelector('#event_end_time').value);
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
	
	jQuery('.edit_event_button').on('click', function(event) {
		let eventmodal = bootstrap.Modal.getOrCreateInstance(eveltmodel_element) // Returns a Bootstrap modal instance
		event_id = event.currentTarget.getAttribute('data-bs-eventid');

		setModalWithData(event_id)
		eventmodal.show()

		
	});

	jQuery('.copy_event_button').on('click', function(event) {
		let eventmodal = bootstrap.Modal.getOrCreateInstance(eveltmodel_element) // Returns a Bootstrap modal instance
		event_id = event.currentTarget.getAttribute('data-bs-eventid');

		setModalWithData(event_id)
		document.querySelector('#modal_event_id').value = "new";
		document.querySelector('#modal_event_pk').value = "new";
		
		eventmodal.show()

		
	});

	

}
function getTimezoneShort(timeZone) {
    return new Intl.DateTimeFormat('en-US', {
        timeZone: timeZone,
        timeZoneName: 'short'
    }).formatToParts(new Date())
        .find(part => part.type == "timeZoneName")
        .value;
}

function formatTz (date){
	const tz = Intl.DateTimeFormat().resolvedOptions().timeZone
	console.log(tz);
	const result = moment.utc(date).tz(tz).format("dddd D MMM yyyy HH:mm z");
	console.log(result);
	return result;
	
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

		var tz_short = Intl.DateTimeFormat().resolvedOptions().timeZone
		var tz = getTzAbbreviation(tz_short)	
		
		
		
		html += `
		<tr>
		<input type="hidden" id="event_id_${i}" name="event_id_${i}" value="${event.id}" />
		<input type="hidden" id="event_location_id_${i}" name="event_location_id_${i}" value="${event.location_id}" />
		<input type="hidden" id="event_start_time_${i}" name="event_start_time_${i}"" value="${event.start_time}" />
		<input type="hidden" id="event_end_time_${i}"" name="event_end_time_${i}"" value="${event.end_time}" />

		
			<td class="">
			<button type="button" class="btn p-0 edit_event_button" data-bs-eventid="${i}"><i class="bi bi-pencil-fill"></i></button>
			</td>
			<td class="small">
			<button type="button" class="btn p-0 delete_event_button" data-bs-eventid="${i}"><i class="bi bi-trash-fill"></i></button>
			</td>
			<td class="small">
			<button type="button" class="btn p-0 copy_event_button" data-bs-eventid="${i}"><i class="bi bi-copy"></i></button>
			</td>
			
			<td class="small">${formatTz(event.start_time)}</td>
			<td class="small">${formatTz(event.end_time)}</td>
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

			setModalWithData(trainingseventid)
			
		} else {
			trainingseventid = 'new'
		}

	})

})()