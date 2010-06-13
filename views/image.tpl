<style>

.image {
    width: 340px;
    padding: 10px;
    text-align: center;
    float: left;
}
.image img {
    width: 320px;
}

.nav {
    margin-bottom: 1em;
}

</style>
<h1>{{ current['name'] }}</h1>

<div class='nav'>
<a href="/">&lt; Images</a> <br />
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


<div class="image">
    <img src="{{ current['url'] }}" />
    <h2>Source</h2>
</div>

<div class="image">
    <img src="/faces/{{ current['index'] }}" />
    <h2>Faces</h2>
</div>

% if prev:
<div class="image">
    <img src="/diff/{{ current['index'] }}/{{ prev['index'] }}" />
    <h2>Diff ({{ diff }})</h2>
</div>
% end


