#!/bin/sh

########################################
#test "$DISPLAY" || export DISPLAY=$(echo $SSH_CLIENT | sed 's/^::ffff:\(.*\)/\1/; s/\([^[:space:]]\+\).*/\1/'):0


########################################
eclipse=${1:-/workopt/eclipse/eclipse-platform-4.2.1-linux-gtk-x86_64/eclipse}
name=${2:-generic}
shift 2

########################################
eclipse_root=/workopt/vruyr/configuration/eclipse
export ECLIPSE_HOME=$eclipse_root/$name
test ! -d $ECLIPSE_HOME && mkdir -p $ECLIPSE_HOME

########################################
if [ -z "$JDK_HOME" ];
then
	export JDK_HOME=/workopt/apps/jdk/1.7.0_05-x64
fi
export JAVA_HOME=$JDK_HOME


########################################
#eval `~/bin/appconfig -r /workopt/vruyr/apps/linux-2.6.32-glibc-2.12-x86_64 python:2.7.3`
#eval `~/bin/appconfig -r /workopt/vruyr/apps/linux-2.6.32-glibc-2.12-x86_64 pypi`
#export PATH=$HOME/bin:$PATH

########################################
args="
-configuration
$ECLIPSE_HOME/configuration
-data
$ECLIPSE_HOME/workspace
-arch x86_64
-vm
$JDK_HOME/bin
-vmargs
-Dorg.eclipse.jdt.ui.codeAssistTimeout=1000
-Dsun.net.client.defaultConnectTimeout=1000
-Xms2G
-Xmx2G
-XX:PermSize=1G
-XX:MaxPermSize=2G
-XX:+UseParallelGC
"

########################################
exec -- "$eclipse" 2>&1 "$@" $args
