let map;

let userLat = 16.5062;
let userLng = 80.6480;

let destinationLat = 16.49;
let destinationLng = 80.63;

let userMarker;
let routeLine;

let facilityLayer;
let alertLayer;

let authMode = "login";


const $ = id => document.getElementById(id);


function init() {

    map = L.map("map").setView(
        [userLat, userLng],
        12
    );


    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            attribution:
                "© OpenStreetMap contributors"
        }
    ).addTo(map);


    facilityLayer =
        L.layerGroup().addTo(map);


    alertLayer =
        L.layerGroup().addTo(map);


    addDemoZones();

    checkMe();

    loadAlerts();

    loadWeather();
}


function scrollToPlanner() {

    document
        .querySelector("#planner")
        .scrollIntoView({
            behavior: "smooth"
        });
}


function addDemoZones() {

    L.circle(
        [
            userLat + 0.01,
            userLng + 0.015
        ],
        {
            radius: 2400,
            color: "#ff5c69",
            fillOpacity: 0.14
        }
    )
    .addTo(map)
    .bindPopup(
        "⚠️ Demonstration high-risk zone"
    );


    L.circle(
        [
            userLat - 0.015,
            userLng - 0.015
        ],
        {
            radius: 1700,
            color: "#42e8bd",
            fillOpacity: 0.12
        }
    )
    .addTo(map)
    .bindPopup(
        "🟢 Safer access zone"
    );
}


function locate() {

    if (!navigator.geolocation) {

        alert(
            "Geolocation is not supported."
        );

        return;
    }


    navigator.geolocation.getCurrentPosition(

        position => {

            userLat =
                position.coords.latitude;

            userLng =
                position.coords.longitude;


            $("startText").value =
                `${userLat.toFixed(5)}, ${userLng.toFixed(5)}`;


            if (userMarker) {

                map.removeLayer(
                    userMarker
                );
            }


            userMarker =
                L.marker([
                    userLat,
                    userLng
                ])
                .addTo(map)
                .bindPopup(
                    "📍 Your current location"
                )
                .openPopup();


            map.setView(
                [
                    userLat,
                    userLng
                ],
                14
            );


            loadWeather();
        },

        () => {

            alert(
                "Location permission was not granted. You can continue with the default map location."
            );

        }
    );
}


async function geocodeDestination() {

    const query =
        $("destText").value.trim();


    if (!query) {

        alert(
            "Enter a destination."
        );

        return;
    }


    try {

        const response =
            await fetch(
                `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(query)}`
            );


        const results =
            await response.json();


        if (!results.length) {

            alert(
                "Destination not found."
            );

            return;
        }


        destinationLat =
            Number(results[0].lat);

        destinationLng =
            Number(results[0].lon);


        map.setView(
            [
                destinationLat,
                destinationLng
            ],
            14
        );


        L.marker([
            destinationLat,
            destinationLng
        ])
        .addTo(map)
        .bindPopup(
            "🎯 Destination"
        )
        .openPopup();


        $("destText").dataset.lat =
            destinationLat;


        $("destText").dataset.lng =
            destinationLng;

    }

    catch (error) {

        alert(
            "Destination search temporarily unavailable."
        );

    }
}


async function analyze() {

    const destination =
        $("destText").value.trim();


    if (!destination) {

        alert(
            "Enter a destination first."
        );

        return;
    }


    if (!$("destText").dataset.lat) {

        await geocodeDestination();
    }


    const destLat =
        Number(
            $("destText").dataset.lat ||
            destinationLat
        );


    const destLng =
        Number(
            $("destText").dataset.lng ||
            destinationLng
        );


    $("result").innerHTML = `

        <div class="loading big">

            🤖 Analyzing live weather,
            disaster signals and route safety…

        </div>
    `;


    try {

        const response =
            await fetch(
                "/api/analyze",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        lat: userLat,

                        lng: userLng,

                        dest_lat: destLat,

                        dest_lng: destLng,

                        destination: destination,

                        disaster:
                            $("disaster").value
                    })
                }
            );


        const data =
            await response.json();


        const weather =
            data.weather || {};


        $("result").innerHTML = `

            <div class="analysis">

                <div class="resultHead">

                    <div>

                        <small>
                            AI SAFETY ASSESSMENT
                        </small>

                        <h3>
                            ${data.disaster}
                        </h3>

                    </div>


                    <b class="badge ${data.level}">
                        ${data.level}
                    </b>

                </div>


                <div class="score">

                    <strong>
                        ${data.risk}
                    </strong>

                    <span>
                        /100 RISK
                    </span>

                    <b>
                        Safety
                        ${data.safety_score}/100
                    </b>

                </div>


                <div class="factor">

                    ${
                        data.factors.length
                        ?
                        data.factors
                            .map(
                                factor =>
                                "• " + factor
                            )
                            .join("<br>")
                        :
                        "• No major live risk factor detected."
                    }

                </div>


                <div class="routeStats">

                    <div>

                        <small>
                            ROUTE
                        </small>

                        <b>
                            ${
                                data.route
                                ?
                                data.route.distance_km
                                + " km"
                                :
                                "Unavailable"
                            }
                        </b>

                    </div>


                    <div>

                        <small>
                            TIME
                        </small>

                        <b>
                            ${
                                data.route
                                ?
                                data.route.duration_min
                                + " min"
                                :
                                "—"
                            }
                        </b>

                    </div>


                    <div>

                        <small>
                            WEATHER
                        </small>

                        <b>
                            ${
                                weather.temperature ??
                                "—"
                            }°C
                        </b>

                    </div>

                </div>


                <div class="recommend">

                    <b>
                        🛡️ AI RECOMMENDATION
                    </b>

                    <p>
                        ${data.recommendation}
                    </p>

                </div>


                <button
                    class="primary wide"
                    onclick="
                        showRoute(
                            ${destLat},
                            ${destLng}
                        )
                    "
                >
                    🗺️ Show Recommended Route
                </button>

            </div>
        `;


        if (
            data.route &&
            data.route.geometry
        ) {

            drawGeoJSON(
                data.route.geometry
            );
        }


        $("weather").innerHTML =
            weatherHTML(weather);


        loadFacilities();

        loadHistory();

    }

    catch (error) {

        $("result").innerHTML = `

            <div class="empty">

                <div>
                    ⚠️
                </div>

                <h3>
                    Analysis failed
                </h3>

                <p>
                    Check your internet connection
                    and try again.
                </p>

            </div>
        `;
    }
}


function drawGeoJSON(geometry) {

    if (routeLine) {

        map.removeLayer(
            routeLine
        );
    }


    const coordinates =
        geometry.coordinates.map(
            point => [
                point[1],
                point[0]
            ]
        );


    routeLine =
        L.polyline(
            coordinates,
            {
                color: "#42e8bd",
                weight: 6,
                opacity: 0.9
            }
        )
        .addTo(map);


    map.fitBounds(
        routeLine.getBounds(),
        {
            padding: [30, 30]
        }
    );
}


async function showRoute(
    destLat,
    destLng
) {

    try {

        const url =
            `https://router.project-osrm.org/route/v1/driving/` +
            `${userLng},${userLat};` +
            `${destLng},${destLat}` +
            `?overview=full&geometries=geojson`;


        const response =
            await fetch(url);


        const data =
            await response.json();


        if (
            data.routes &&
            data.routes[0]
        ) {

            drawGeoJSON(
                data.routes[0].geometry
            );
        }


        document
            .querySelector("#mapSection")
            .scrollIntoView({
                behavior: "smooth"
            });

    }

    catch (error) {

        alert(
            "Routing service unavailable."
        );
    }
}


async function loadFacilities() {

    facilityLayer.clearLayers();


    const response =
        await fetch(
            `/api/facilities?lat=${userLat}&lng=${userLng}`
        );


    const data =
        await response.json();


    const icons = {

        hospital: "🏥",

        clinic: "🏥",

        police: "🚔",

        fire_station: "🚒",

        shelter: "🏠",

        ambulance_station: "🚑"

    };


    (data.facilities || [])
        .forEach(facility => {

            L.marker([
                facility.lat,
                facility.lon
            ])
            .addTo(facilityLayer)
            .bindPopup(`

                ${icons[facility.type] || "🚨"}

                <b>
                    ${facility.name}
                </b>

                <br>

                ${facility.type}

            `);

        });
}


async function loadWeather() {

    try {

        const response =
            await fetch(
                `https://api.open-meteo.com/v1/forecast?` +
                `latitude=${userLat}` +
                `&longitude=${userLng}` +
                `&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,wind_gusts_10m,visibility,weather_code`
            );


        const data =
            await response.json();


        $("weather").innerHTML =
            weatherHTML(
                data.current || {}
            );

    }

    catch (error) {

        console.log(error);
    }
}


function weatherHTML(weather) {

    return `

        <div class="weatherGrid">

            <div>
                <small>
                    TEMPERATURE
                </small>

                <b>
                    ${weather.temperature_2m ?? "—"}°C
                </b>
            </div>


            <div>
                <small>
                    HUMIDITY
                </small>

                <b>
                    ${weather.relative_humidity_2m ?? "—"}%
                </b>
            </div>


            <div>
                <small>
                    RAIN
                </small>

                <b>
                    ${weather.precipitation ?? "—"} mm
                </b>
            </div>


            <div>
                <small>
                    WIND
                </small>

                <b>
                    ${weather.wind_speed_10m ?? "—"} km/h
                </b>
            </div>


            <div>
                <small>
                    GUST
                </small>

                <b>
                    ${weather.wind_gusts_10m ?? "—"} km/h
                </b>
            </div>


            <div>
                <small>
                    VISIBILITY
                </small>

                <b>
                    ${
                        weather.visibility
                        ?
                        Math.round(
                            weather.visibility / 1000
                        )
                        :
                        "—"
                    }
                    km
                </b>
            </div>

        </div>
    `;
}


async function loadAlerts() {

    try {

        const response =
            await fetch(
                "/api/alerts"
            );


        const data =
            await response.json();


        const events =
            data.events || [];


        if (!events.length) {

            $("alertsList").innerHTML = `

                <div class="empty small">

                    No recent GDACS events returned.

                </div>
            `;

            return;
        }


        $("alertsList").innerHTML =
            events
            .slice(0, 8)
            .map(event => {

                const properties =
                    event.properties || event;


                const title =
                    properties.name ||
                    properties.description ||
                    properties.eventtype ||
                    "Disaster event";


                return `

                    <div class="alertItem">

                        <span>
                            ⚠️
                        </span>

                        <div>

                            <b>
                                ${title}
                            </b>

                            <small>
                                Global disaster-awareness feed • GDACS
                            </small>

                        </div>

                    </div>
                `;

            })
            .join("");

    }

    catch (error) {

        $("alertsList").innerHTML = `

            <div class="empty small">

                Live alert feed temporarily unavailable.

            </div>
        `;
    }
}


function openEmergency() {

    $("emergencyModal")
        .classList
        .add("show");
}


function openAuth(mode) {

    authMode = mode;


    $("authModal")
        .classList
        .add("show");


    $("authName").style.display =
        mode === "register"
        ? "block"
        : "none";


    $("authTitle").textContent =
        mode === "register"
        ? "Create Account"
        : "Login";
}


function closeModal(id) {

    $(id)
        .classList
        .remove("show");
}


function toggleAuth() {

    openAuth(
        authMode === "login"
        ? "register"
        : "login"
    );
}


async function submitAuth() {

    const body = {

        name:
            $("authName").value,

        email:
            $("authEmail").value,

        password:
            $("authPassword").value

    };


    const response =
        await fetch(
            authMode === "register"
            ? "/api/register"
            : "/api/login",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body:
                    JSON.stringify(body)
            }
        );


    const data =
        await response.json();


    if (!data.ok) {

        $("authError")
            .textContent =
            data.error;

        return;
    }


    closeModal(
        "authModal"
    );


    checkMe();

    loadHistory();
}


async function checkMe() {

    const response =
        await fetch(
            "/api/me"
        );


    const data =
        await response.json();


    if (data.logged_in) {

        $("userLabel").innerHTML =
            `Hi, ${data.name} · <a href="/logout">Logout</a>`;

        loadHistory();

    }

    else {

        $("userLabel").innerHTML = "";
    }
}


async function loadHistory() {

    const response =
        await fetch(
            "/api/history"
        );


    const data =
        await response.json();


    if (
        !data.items ||
        !data.items.length
    ) {

        $("history").innerHTML =
            "No saved analyses yet.";

        return;
    }


    $("history").innerHTML =
        data.items
        .map(item => `

            <div class="historyRow">

                <b>
                    ${item.disaster}
                </b>

                <span>
                    ${item.level}
                    ·
                    ${item.risk}/100
                </span>

            </div>
        `)
        .join("");
}


init();