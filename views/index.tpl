<style>
ul.images {
    float: left;
    margin: 0;
    padding: 0;
}
ul.images li {
    float: left;
    width: 130px;
    padding: 5px;
    margin: 0;
    text-align: center;
    list-style: none;
}
ul.images li img {
    width: 120px;
}
ul.pagination {
    padding: 0;
    margin: 0 0 1em 0;
}
ul.pagination li {
    list-style: none;
    display: inline;
    padding: 0;
    margin: 0;
}
</style>
<h1>Images</h1>
<ul class="pagination">
    <li>Pages:</li>
% for page in pages:
    <li><a href="?page={{ page }}">{{ page }}</a></li>
% end
</ul>

<ul class="images">
% for image in images:
    <li>
        <a href="image/{{ image['index'] }}">
            <img src="{{ image['url'] }}" />
            {{ image['name'] }}
        </a>
    </li>
% end
</ul>