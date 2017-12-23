#!/usr/bin/env python3
# Python Standard Library
import sys; assert sys.version_info[:2] in [(3, 6)]
import asyncio, os, shutil, itertools, plistlib, json
# https://github.com/xattr/xattr
import xattr


IGNORED_ATTRIBUTES = {
	"com.apple.quarantine",
	"com.apple.FinderInfo",
	"com.apple.cs.CodeDirectory",
	"com.apple.cs.CodeRequirements",
	"com.apple.cs.CodeRequirements-1",
	"com.apple.cs.CodeSignature",
	"com.apple.cs.CodeEntitlements",
	"com.apple.metadata:kMDItemIsScreenCapture",
	"com.apple.metadata:kMDItemScreenCaptureGlobalRect",
	"com.apple.metadata:kMDItemScreenCaptureType",
	"com.apple.TextEncoding",
	"com.apple.metadata:kMDItemDownloadedDate",
	"com.apple.metadata:kMDItemWhereFroms",
	"com.apple.diskimages.fsck",
	"com.apple.diskimages.recentcksum",
	"com.apple.AddressBook.ImageTransform.ABClipRect_1",
	"com.apple.AddressBook.ImageTransform.ABClipRect_1_hash",
	"com.apple.assetsd.assetType",
	"com.apple.assetsd.avalanche.type",
	"com.apple.assetsd.creatorBundleID",
	"com.apple.assetsd.customCreationDate",
	"com.apple.assetsd.favorite",
	"com.apple.assetsd.hidden",
	"com.apple.assetsd.thumbnailCameraPreviewImageAssetID",
	"com.apple.assetsd.trashed",
	"com.apple.assetsd.UUID",
	"com.apple.bird.graveyard.size#N",
	"com.apple.bird.iwork-sharing#N",
	"com.apple.clouddocs.enclosure-docid",
	"com.apple.clouddocs.signature",
	"com.apple.cpl.original",
	"com.apple.cscachefs",
	"com.apple.genstore.origposixname",
	"com.apple.GeoServices.SHA1",
	"com.apple.icloud.itemName",
	"com.apple.installd.container_bundle_id",
	"com.apple.installd.container_creation_os_build",
	"com.apple.iwork.documentUUID#PS",
	"com.apple.iwork.documentUUID.synced",
	"com.apple.iwork.folder-modification-seed#PS",
	"com.apple.lastuseddate#PS",
	"com.apple.LaunchServices.OpenWith",
	"com.apple.metadata:com_apple_backup_excludeItem",
	"com.apple.metadata:com_apple_mail_dateReceived",
	"com.apple.metadata:com_apple_mail_dateSent",
	"com.apple.metadata:com_apple_mail_isRemoteAttachment",
	"com.apple.metadata:FileSyncAgentExcludeItem",
	"com.apple.metadata:kMDItemLastUsedDate",
	"com.apple.metadata:kMDItemOriginSenderDisplayName",
	"com.apple.Preview.synced.UIstate.v1",
	"com.apple.quicklook.thumbdict#CP",
	"com.apple.quicklook.thumbmetadata#CP",
	"com.apple.ubd.prsid",
	"com.apple.xcode.PlistType",
	"com.apple.metadata:kMDLabel_5rqllyihffya4ljoqs47iox3xa",
	"com.apple.metadata:kMDLabel_k7jeljivgytc6d4e66ugc2y4zq",
	"com.apple.metadata:kMDLabel_nfzp5ybs3hh6irug7lx2srtevm",
	"com.apple.metadata:kMDLabel_p67nzalsktwiaoec6iiimsyemu",
	"com.apple.metadata:kMDLabel_rstdxggekv6sgukat6ga23hdge",
	"com.apple.metadata:kMDLabel_wp4k36fapu643uvrmhqa2mwloq",

	"com.apple.ResourceFork",

	"x.attribute.dft.dx.tpi.1.1",
	"com.omnigroup.OmniFocusModel.BackupReason",
	"NSImageMetadata",
	"lumberjack.log.archived",
}


async def main(*, args=None, loop=None):
	captured_xattrs = {}

	fo = sys.stderr
	new_line(fo=fo)
	for path in args:
		for root, dirs, files in os.walk(path):
			for dir_entry in itertools.chain([""], dirs, files):
				path = os.path.join(root, dir_entry)
				last_line_set(path, fo=fo)

				attrs = {}
				path_xattr = xattr.xattr(path, options=xattr.XATTR_NOFOLLOW)
				for name in path_xattr.list():
					if dir_entry == "Icon\r" and name == "com.apple.ResourceFork":
						continue
					if name in IGNORED_ATTRIBUTES:
						continue
					value = None
					if name == "com.apple.metadata:_kMDItemUserTags":
						value = plistlib.loads(path_xattr.get(name))
						if len(value) < 1:
							name = None
					if name == "com.apple.metadata:kMDItemFinderComment":
						value = plistlib.loads(path_xattr.get(name))
					if name is not None:
						attrs[name] = value
				if not attrs:
					continue
				captured_xattrs[path] = attrs

				last_line_clear(fo=fo, flush=False)
				fo.write(path)
				fo.write("\n")
				new_line(fo=fo, flush=False)

	last_line_clear(fo=fo)

	json.dump(captured_xattrs, sys.stdout, indent="\t")
	sys.stdout.write("\n")
	sys.stdout.flush()


def new_line(*, fo, flush=True):
	fo.write("\n")
	if flush:
		fo.flush()


def last_line_clear(*, fo, flush=True):
	fo.write("\x1b[1F") # "CSI n F"
	fo.write("\x1b[0K") # "CSI n K"
	if flush:
		fo.flush()


def last_line_set(text, *,
	fo=sys.stderr,
	terminal_size=shutil.get_terminal_size(fallback=(178, 45)),
	clip=True, # TODO Change this to an enum ("left", "middle", "right")
	replacement=" ... ",
	flush=True,
):
	text_len = len(text)
	if text_len > terminal_size.columns:
		extra = text_len - terminal_size.columns + len(replacement)
		left = text_len // 2 + text_len % 2
		right = left
		left -= extra // 2
		right += extra - (extra // 2)
		text = text[:left] + replacement + text[right:]
	last_line_clear(fo=fo, flush=False)
	fo.write(text)
	fo.write("\n")
	if flush:
		fo.flush()


def _smain():
	if sys.platform == "win32":
		loop = asyncio.ProactorEventLoop()
		asyncio.set_event_loop(loop)
	else:
		loop = asyncio.get_event_loop()
	loop.run_until_complete(main(args=sys.argv[1:], loop=loop))


if __name__ == "__main__":
	try:
		sys.exit(_smain())
	except KeyboardInterrupt:
		sys.stderr.write("\n")
