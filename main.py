import json

with open("data/festival.json", encoding="utf-8") as file:
    festival = json.load(file)

venues = festival["venues"]
artists = festival["artists"]
performances = festival["performances"]

print(festival["name"])
print(f"From {festival['first_day']} to {festival['last_day']}")
print(f"{len(venues)} venues, {len(artists)} artists, {len(performances)} performances")

print("\nVenues:")
total_seats = 0
for venue in venues:
    print(f"- {venue['name']}: {venue['capacity']} seats ({venue['address']})")
    total_seats += venue["capacity"]
print(f"Total: {total_seats} seats")

kind_counts = {}
for performance in performances:
    kind = performance["kind"]
    if kind in kind_counts:
        kind_counts[kind] += 1
    else:
        kind_counts[kind] = 1

print()
for kind in kind_counts:
    print(f"{kind}: {kind_counts[kind]}")

print("\nAt Le Kiosque:")
for performance in performances:
    if performance["venue"] == "le-kiosque":
        print(f"- {performance['start']} {performance['title']}")

longest = performances[0]
for performance in performances:
    if performance["duration_minutes"] > longest["duration_minutes"]:
        longest = performance
print(f"\nLongest: {longest['title']} ({longest['duration_minutes']} min)")

for performance in performances:
    if performance["kind"] == "workshop":
        print(
            f"\n{performance['title']} on {performance['start'][:10]}: "
            f"{len(performance['participants'])}/"
            f"{performance['max_participants']} registered"
        )

artist_counts = {}
for performance in performances:
    if "artist" in performance:
        artist = performance["artist"]
        artist_counts[artist] = artist_counts.get(artist, 0) + 1
    if "host" in performance:
        host = performance["host"]
        artist_counts[host] = artist_counts.get(host, 0) + 1
    if "acts" in performance:
        for artist in performance["acts"]:
            artist_counts[artist] = artist_counts.get(artist, 0) + 1
    if "teacher" in performance:
        teacher = performance["teacher"]
        artist_counts[teacher] = artist_counts.get(teacher, 0) + 1

most_performances = 0
for count in artist_counts.values():
    if count > most_performances:
        most_performances = count

most_frequent_artists = []
for artist in artist_counts:
    if artist_counts[artist] == most_performances:
        most_frequent_artists.append(artist)
print(f"\nOn stage {most_performances} times: {', '.join(most_frequent_artists)}")

days = []
for performance in performances:
    day = performance["start"][:10]
    if day not in days:
        days.append(day)

venue_names = {}
for venue in venues:
    slug = venue["name"].lower().replace("é", "e").replace("â", "a").replace(" ", "-")
    venue_names[slug] = venue["name"]

day = input("\nDay (YYYY-MM-DD): ").strip()
while day not in days:
    print(f"No performance on {day!r}. Days: {', '.join(days)}")
    day = input("Day (YYYY-MM-DD): ").strip()

print(f"Programme for {day}:")
for performance in performances:
    if performance["start"][:10] == day:
        time = performance["start"][11:]
        venue_name = venue_names[performance["venue"]]
        print(f"{time} | {venue_name} | {performance['title']} ({performance['kind']})")
