#!/bin/bash

set -e

optstring='i:o:bs:p:c:'

if [ "$1" != "--options-are-normalized" ];
then
	options=`getopt -n "$(basename $0)" -s bash -o $optstring -- "$@"`
	test $? -ne 0 && exit 1
	eval exec "$0" --options-are-normalized $options
fi
shift

inputdir=
outputdir=
openbrowser=
PROJECT_NAME=$(basename $PWD)
configOverride=
while getopts $optstring opt;
do
	case $opt in
	'i')
		inputdir=$OPTARG
		;;
	'o')
		outputdir=$OPTARG
		;;
	'b')
		openbrowser=1
		;;
	'p')
		PROJECT_NAME=$OPTARG
		;;
	'c')
		configOverride=$OPTARG
		;;
	*)
		;;
	esac
done
let OPTIND-- && shift $OPTIND && OPTIND=1

test "$inputdir"  || inputdir=$(hg root)/src
test "$outputdir" || outputdir=$(hg root)/linux/doxy
test "$outputdir" || outputdir=$(mktemp -d /scratch2/$USER/doxy.XXXXXXXXXX)

echo "Input: $inputdir"
echo "Output: $outputdir"

test -d "$outputdir" || mkdir "$outputdir"

lockfile=$(cd $outputdir && echo $(pwd)/.lock)
test "$lockfile" || { echo "can't figure out where to put the lock file" >&2; exit 1; }
if test -e "$lockfile";
then
	echo "Quitting (locked): $(dirname $lockfile)"
	exit 1
else
	touch $lockfile
fi

function cleanup()
{
	test -f "$mainpage" && rm "$mainpage"
	rm $lockfile
}

trap "cleanup" EXIT SIGINT SIGTERM

SCM_URL=$(hg paths default)
LAST_CHANGE="<pre>"$(hg --config extensions.graphlog= log -r '.:0 and branch(.)' --stat -G -l3 --config 'ui.logtemplate="{node|short} {date|isodate} {author|user} {branch} {tags} {desc|strip|firstline}\n"')"</pre>"
VERSION_STRING=$(hg log -r . --template '{branch}-{node|short}')

mainpage=$(mktemp)
cat >$mainpage <<ENDOFTEXT
/**
\mainpage
This documentation was generated from following code:
<table style="width: 100%; font-family: monospace;">
<tr><td style="width: 10em;">URL</td><td>$SCM_URL</td></tr>
<tr><td>Recent Changes</td><td>$LAST_CHANGE $SERVER_TIMEZONE</td></tr>
</table>
<br>
\see main

<br>
To improve this documentation, please add/edit <a href="http://www.doxygen.org/docblocks.html">doxygen</a> comments in the code.
*/
ENDOFTEXT

(
	cat <<ENDOFTEXT
		#################### Project related options
		PROJECT_NAME           = $PROJECT_NAME
		PROJECT_NUMBER         = $VERSION_STRING
		OUTPUT_DIRECTORY       = $outputdir
		CREATE_SUBDIRS         = YES
		SEPARATE_MEMBER_PAGES  = YES
		EXTENSION_MAPPING      = h=C++ c=C++
		BUILTIN_STL_SUPPORT    = YES
		SYMBOL_CACHE_SIZE      = 7
		LOOKUP_CACHE_SIZE      = 4

		#################### Build related options
		EXTRACT_ALL             = YES
		EXTRACT_PRIVATE         = YES
		EXTRACT_STATIC          = YES
		EXTRACT_LOCAL_METHODS   = YES
		EXTRACT_ANON_NSPACES    = YES
		INTERNAL_DOCS           = YES
		CASE_SENSE_NAMES        = NO
		GENERATE_DEPRECATEDLIST = YES
		GENERATE_TODOLIST       = YES
		GENERATE_TESTLIST       = YES
		GENERATE_BUGLIST        = YES

		#################### Options related to warning and progress messages
		QUIET                  = NO
		WARN_LOGFILE           = $outputdir/doxygen-warnings.log

		#################### Input related options
		INPUT                  = $mainpage $inputdir
		RECURSIVE              = YES
		EXCLUDE_PATTERNS       = */.git/* */.hg/* */.svn/*

		#################### Source browsing related options
		SOURCE_BROWSER         = YES
		INLINE_SOURCES         = YES
		REFERENCED_BY_RELATION = YES
		REFERENCES_RELATION    = YES

		#################### HTML related options
		HTML_DYNAMIC_SECTIONS  = YES
		#GENERATE_ECLIPSEHELP   = YES
		#ECLIPSE_DOC_ID         =
		SEARCHENGINE           = YES
		SERVER_BASED_SEARCH    = YES
		GENERATE_TREEVIEW      = NO

		#################### LaTeX related options
		GENERATE_LATEX         = NO

		#################### Preprocessor related options
		ENABLE_PREPROCESSING = YES
		MACRO_EXPANSION      = YES

		#################### External reference options
#		TAGFILES               =	path/to/tag1=path/to/html1 \
#									path/to/tag2=path/to/html2
		GENERATE_TAGFILE       = $outputdir/doxygen.tag
		ALLEXTERNALS           = YES
		EXTERNAL_GROUPS        = YES

		#################### Dot options
		HAVE_DOT               = YES
		DOT_NUM_THREADS        = 5
		UML_LOOK               = NO
		TEMPLATE_RELATIONS     = YES
		INCLUDE_GRAPH          = YES
		INCLUDED_BY_GRAPH      = YES
		CALL_GRAPH             = NO
		CALLER_GRAPH           = NO
		DIRECTORY_GRAPH        = YES
		DOT_IMAGE_FORMAT       = svg
		INTERACTIVE_SVG        = YES
		DOT_GRAPH_MAX_NODES    = 10000
		MAX_DOT_GRAPH_DEPTH    = 0
		DOT_TRANSPARENT        = YES
		DOT_MULTI_TARGETS      = YES
		GENERATE_LEGEND        = YES
		DOT_CLEANUP            = NO
ENDOFTEXT
	test "$configOverride" -a -e "$configOverride" && cat $configOverride
) | PATH=/linopt/graphviz/graphviz-2.28.0/bin:$PATH /home/vruyrg/apps/doxygen/1.8.3/bin/doxygen -

#echo 'a.anchor:target + div.memitem div.memproto { border: 1px solid red; }' >>$outputdir/html/doxygen.css

echo "The documentation is in this folder: $outputdir/html"
test "$openbrowser" && xdg-open "$outputdir/html/index.html"
exit 0
