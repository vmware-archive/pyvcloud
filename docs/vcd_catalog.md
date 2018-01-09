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
          vcd catalog upload my-catalog photon.ova
              Upload OVA to a catalog.
  
          vcd catalog download my-catalog photon.ova
              Download OVA from catalog.
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
              Publish and share catalog across all organizations.
  
          vcd catalog unshare my-catalog
              Stop sharing a catalog across all organizations.
  
          vcd catalog update my-catalog -n 'new name' -d 'new description'
              Update the name and/or description of a catalog.
      

Options:
  -h, --help  Show this message and exit.

Commands:
  acl           work with catalog acl
  change-owner  change the ownership of catalog
  create        create a catalog
  delete        delete a catalog or item
  download      download item from catalog
  info          show catalog or item details
  list          list catalogs or items
  share         share a catalog to all organization
  unshare       unshare a catalog from all organization
  update        rename catalog and/or change catalog description
  upload        upload file to catalog

```
