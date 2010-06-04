
<h1>{{ current['name'] }}</h1>

<div>
% if prev:
<a href="/image/{{ prev['index'] }}">&lt;&lt;--</a>
% end
% if prev and next:
|
% end
% if next:
<a href="/image/{{ next['index'] }}">--&gt;&gt;</a>
% end
</div>

<br />

<img src="{{ current['url'] }}" />

% if prev:
<img src="/diff/{{ current['index'] }}/{{ prev['index'] }}" />
% end

