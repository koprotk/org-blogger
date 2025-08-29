# myBlog
My blog project, consist in the creation of my own post on org mode and then publish it with a small script in python, the title, and the tags are managed automatically by the script through the package `orgparse`. The export from Org to Html is made by Emacs itself. The process is completely unpainful.


## First
Write your post on a org file on the `draft` folder:

## Second 
Put your google credentials (a `json` file that google provide it) on the `config` folder

## Third
When you are sure to the post is ready to be publish run it.

How to run it? On a terminal run:

    python3 scripts/publish_on_bloggerv2.py myorgfile.org

And that's it.

## PS
If you wanna a front image on your post, you can link it as image (should need image extension) if you have a web link to the image that doesn't have image extension on the url you need to put it as HTML tag.
