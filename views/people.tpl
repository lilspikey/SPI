<ul>
% for person in people:
    <li>
        <a href="{{ person['url'] }}">{{ person['name'] }}</a>
    </li>
% end
</ul>