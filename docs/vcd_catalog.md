```
Usage: vcd catalog [OPTIONS] COMMAND [ARGS]...

  Work with catalogs in current organization.

      Examples
          vcd catalog list
              Get list of catalogs in current organization.
  
          vcd catalog create my-catalog -d 'My Catalog of Templates'
              Create catalog.
  
          vcd catalog create 'my catalog'
              Create catalog with white spaces in the name.
  
          vcd catalog delete my-catalog
              Delete catalog.
  
          vcd catalog info my-catalog
              Get details of a catalog.
  
          vcd catalog info my-catalog linux-template
              Get details of a catalog item.
  
          vcd catalog list my-catalog
              Get list of items in a catalog.
  
          vcd catalog list '*'
          vcd catalog list \*
              Get list of items in all catalogs in current organization.
  
          vcd catalog upload my-catalog installer.iso
              Upload media file to a catalog.
  
          vcd catalog download my-catalog installer.iso
              Download media file from catalog.
  
          vcd catalog delete my-catalog installer.iso
              Delete media file from catalog.
  
          vcd catalog share my-catalog
              Publish and share catalog accross all organizations.
  
          vcd catalog unshare my-catalog
              Stop sharing a catalog.
      

Options:
  -h, --help  Show this message and exit.

Commands:
  create    create a catalog
  delete    delete a catalog or item
  download  download item from catalog
  info      show catalog or item details
  list      list catalogs or items
  share     share a catalog
  unshare   unshare a catalog
  upload    upload file to catalog

```
