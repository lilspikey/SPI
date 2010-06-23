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
% for person in people:
    <li>
        <a href="{{ person['url'] }}">
            <img src="{{ person['image_url'] }}" />
        </a>
        <div>{{ person['name'] }}</div>
    </li>
% end
</ul>