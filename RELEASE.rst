
Steps to release a new version
------------------------------

Preparing for the release

 - Check out a branch named for the version:
    `git checkout -b release-1.1.1`
 - Change version in `sceptremods/__init__.py`
 - Update CHANGELOG.rst with changes made since last release:
    `git log --pretty=format:"%s" | tail -100 | sed "s/^/- /"`
 - add changed files:
    `git add src/sceptremods/__init__.py CHANGELOG.md`
 - Commit changes:
    `git commit -m "Release 1.1.1"`
 - Create tag:
    `git tag -am "Release 1.1.1" 1.1.1`
 - Push branch up to github:
    `git push -u origin release-1.1.1`
 - Push tag:
    `git push --tags`
 - Open a PR for the release, ensure that tests pass

Releasing

 - Checkout master locally:
    `git checkout master; git pull; git fetch`
 - Merge PR into master:
    `git merge release-1.1.1; git push`
 - Update github release page: https://github.com/ashleygould/aws-sceptremods/releases.  Use the contents of the latest CHANGELOG entry for the body.


