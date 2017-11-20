== Lyrics Scraper ==
== (written in Python) ==

This simple application automatically crawl all the links found in http://www.azlyrics.com,
extract spotted lyrics, and store them in a database file called 'lyrics.sqlite'.

You may need to install DB Browser for SQLite in your system to open the 'lyrics.sqlite'
file. DB Browser for SQLite (free) could be downloaded through the following link http://sqlitebrowser.org

== How to Run the Application ? ==  

1. Download all the files found in the 'Standalone Application (Windows)' folder and
  move them to a designated location in your system.
2. Execute azl.exe

Unfortunately, the standalone application will only work on Windows. For MAC OSX user,
please execute the 'azl.py' file found in the 'Source Code' folder using Python Shell
installed in your system. Please do note that once the program is executed,
it will create a “lyrics.sqlite” file in the same folder. To view the retrieved data,
please open the “lyrics.sqlite” file. To see the sample result, please navigate to the
'Sample Result' folder.
