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
.nav {
    clear: both;
}
</style>
<h1>Images</h1>



<ul class="pagination">
    <li>Pages:</li>
% prev_shown = False
% for page in pages:
    % if page == 1 or page == len(pages) or (abs(current_page-page) < 10):
        % prev_shown = True
    <li><a href="?page={{ page }}{{ '&amp;has_faces=%s' % has_faces if has_faces else '' }}{{ '&amp;diff_gt=%s' % diff_gt if diff_gt else '' }}{{ '&amp;' if date else '' }}{{ '&amp;'.join(['date=%s' % d for d in date]) if date else '' }}"
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
            % if has_faces:
            <img src="/faces/{{ image['index'] }}" />
            % else:
            <img src="{{ image['url'] }}" />
            % end
            {{ image['name'] }}
        </a>
    </li>
% end
</ul>

<div class="nav">
    <ul>
        <li><a href="/checkins">Checkins</a></li>
        <li><a href="/people">People</a></li>
        <li>
            <form action="/" method="get">
                <input type="checkbox" name="has_faces" id="has_faces" 
                % if has_faces:
                checked="checked"
                % end
                />
                <label for="has_faces">has faces</label>
                <input type="text" size="4" name="diff_gt" id="diff_gt" value="{{ diff_gt if diff_gt else '' }}" />
                <label for="diff_gt">diff gt</label>
                <input type="submit" value='Query' />
            </form>
        </li>
        <li><a href="/diff/calc">Calculate Diffs (takes a while)</a></li>
        <li>
            <form action="/faces/detect" method="get">
                <input type="text" size="4" name="diff_gt" id="diff_gt" value="{{ diff_gt if diff_gt else '' }}" />
                <label for="diff_gt">diff gt</label>
                <input type="submit" value='Detect Faces' />
            </form>
        </li>
        <li><a href="/init">Init DB</a></li>
    </ul>
</div>