// LoadCompositeAPIData loader = new LoadCompositeAPIData();

// load a single Composite Graph JSON Payload
LoadCompositeAPIData.loadSingleJsonGraphPayload('https://gist.githubusercontent.com/prescod/13302ecbd08fc3fe92db7d6ee4614d25/raw/c88949d2170c7c11f94958ec672ec8b972cc10d4/composite.json');

// load anoter single one slightly less efficiently
LoadCompositeAPIData.loadJsonSet('https://gist.githubusercontent.com/prescod/ffa992a7218906ab0dcf160b5d755259/raw/f9d40587a2ba9b04275241723637ed571bd55617/Graph%2520Gist');

// load a set of 3 Composite Graph JSONs in a distributed set
LoadCompositeAPIData.loadJsonSet('https://gist.githubusercontent.com/prescod/6f3aebafde63971d1093549c3bef4e41/raw/8885df2618ece474c196d5d94b594dd2b5961c71/csvw_metadata.json');

// load a single-file bundle of 3 Composite Graph JSONs
LoadCompositeAPIData.loadJsonSet('https://gist.githubusercontent.com/prescod/6220fa27d8493be954be949c9f57f2b2/raw/b603a4d11ef20f0a30e79260322baa52f969068d/out.bundle.json');

System.debug('SUCCESS! SUCCESS! SUCCESS! SUCCESS! SUCCESS! SUCCESS! SUCCESS! ');
// experimentally, much more than 15 hits a cumulative
// maximum time allotted for callout error
//
// for (Integer i = 0; i < 15; i++) {
//     loader.loadSingleJsonGraphPayload('https://gist.githubusercontent.com/prescod/13302ecbd08fc3fe92db7d6ee4614d25/raw/c88949d2170c7c11f94958ec672ec8b972cc10d4/composite.json');
//     System.debug(i);
// }

