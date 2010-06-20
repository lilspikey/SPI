<style>
ul {
    list-style: none;
    padding: 0;
    margin: 0;
}
li {
    text-align: center;
    padding: 10px;
    margin: 0;
    float: left;
}
</style>
<ul>
% for checkin in checkins:
    <li>
        <a href="/?has_faces=on&amp;date={{ checkin['created'] }}"><img src="{{ checkin['image_url'] }}" /></a>
        <div>{{ checkin['name'] }} ({{ checkin['possible'] }})</div>
        <div><a href="/?has_faces=on&amp;date={{ checkin['created'] }}">{{ checkin['created'] }}</a></div>
        <div><a href="http://gowalla.com{{ checkin['url'] }}">{{ checkin['url'] }}</a></div>
    </li>
% end
</ul>