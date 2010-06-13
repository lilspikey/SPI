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
ul.pagination li a.selected {
    color: black;
    font-weight: bold;
    text-decoration: none;
}
</style>
<h1>Images</h1>
<ul class="pagination">
    <li>Pages:</li>
% prev_shown = False
% for page in pages:
    % if page == 1 or page == len(pages) or (abs(current_page-page) < 10):
        % prev_shown = True
    <li><a href="?page={{ page }}"
        % if page == current_page:
        class="selected"
        % end
        >{{ page }}</a></li>
    % else:
        % if prev_shown:
        <li>...</li>
        % end
        % prev_shown = False
    % end
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