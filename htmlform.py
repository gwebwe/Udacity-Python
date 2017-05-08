form = """
<form method="post">
	What is your birthday?
	<br>
	<label> Month
	<input type="text" name="month" value="%(month)s">
	</label>
	<label> Day
	<input type="text" name="day" value="%(day)s">
	</label>
	<label> Year
		<input type="text"  name="year" value="%(year)s">
	</label>
	<div style="color:red"> %(error)s</div>
	<br>
	<input type="submit">
</form>
<form action="/rot13" method="get">
    <input type="submit" value="ROT13">
</form>
<form action="/usersignup" method="get">
    <input type="submit" value="User Signup">
</form>
"""
rot13page="""
    <form method="post">
    <h2> ROT13 Table </h2>
        <textarea rows="10" cols="50" name="text">%(text)s</textarea>
    <br>
    <input type="submit">
    </form>

"""

usersignupform="""
    <form method="post">
    <label> Username
    <input type="text" name="username" value="%(user)s">
    </label>
    <span style="color:red">%(usererror)s</span>
    <br>
    <label> Password
    <input type="password" name="password">
    </label>
    <span style="color:red">%(pwerror)s</span>
    <br>
    <label> Verify password
    <input type="password" name="verify">
    </label>
    <span style="color:red">%(matchingerror)s</span>
    <br>
    <label> Email(Optional)
    <input type="text" name="email" value="%(email)s">
    </label>
    <br>
    <br>
    <input type="submit">
    </form>
"""