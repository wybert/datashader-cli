"""Console script for datashader_cli."""

import click
import datetime
import colorcet as cc
import sys


@click.group()
def main(args=None):
    """Quick visualization of large datasets using CLI based on datashader. Supported data format: csv, parquet, hdf, feather, geoparquet, shapefile, geojson, geopackage, etc.
    
    Examples:

    1. Create a shaded scatter plot of points and save it to png file, set background color to black.
    
    `datashader_cli points nyc_taxi.parquet --x pickup_x --y pickup_y pickup-scatter.png --background black`

    2. Visualize the geospaital data, support Geoparquet, shapefile, geojson, geopackage, etc.

    `datashader_cli points data.geo.parquet data.png --geo true`

    3. Use matplotlib to render the image

    `datashader_cli points data.geo.parquet data.png --geo true --matplotlib true`


    """
    
    return 0



# Define a command
@click.command()
# Specify the data path as an argument
@click.argument('data_path', type=click.Path(exists=True), required=True)
@click.argument('output_apth',default = None, type = str, required=True)

# Define various options for customization
@click.option('--x', default='x', type = str, required=False, help = 'Name of the x column, if geo=True, x is optional')
@click.option('--y', default='y', type = str, required=False, help = 'Name of the y column, if geo=True, y is optional')
@click.option('--w', default=600,type = int, required=False, help = 'How many pixels wide to make the image')
@click.option('--h', default=600, type = int,required=False, help = 'How many pixels high to make the image')
@click.option('--x_range',default=None,type = str, required=False, help = 'Range of the x axis, in the form of "xmin,xmax"')
@click.option('--y_range',default=None,type = str, required=False, help = 'Range of the y axis, in the form of "ymin,ymax"')
@click.option('--agg', default = None, type = str, required=False, help = """Aggregation function, e.g. "mean", "count", "sum", see datashader docs (https://datashader.org/api.html#reductions) for more options""")
@click.option('--agg_col', default = None, type = str, required=False, help = """Column to aggregate on, e.g. "value" """)
@click.option('--by',default=None,type= str, required=False, help = """Column to group by, e.g. "category", see datashader docs (https://datashader.org/api.html#reductions) for more options""")
@click.option('--spread_px', default=None, type =int,required=False, help = 'How many pixels to spread points by, e.g. 1, see https://datashader.org/api.html#datashader.transfer_functions.spread')
@click.option('--how',default="eq_hist", type =str,required=False, help = 'How to map values to colors, valid strings are ‘eq_hist’ [default], ‘cbrt’ (cube root), ‘log’ (logarithmic), and ‘linear’. see https://datashader.org/api.html#datashader.transfer_functions.set_background ')
@click.option('--cmap',default="fire", required=False, type = str, help = 'Name of the colormap, see https://colorcet.holoviz.org for more options')
@click.option('--geo',default=False, required=False, type = bool, help = 'Whether the data is geospatial, if True, x and y are optional, need Geopandas installed to use this option, supported data format: Geoparquet, shapefile, geojson, geopackage, etc.')
@click.option('--background',default=None, required=False, type = str, help = """Background color, e.g. "black", "white", "#000000", "#ffffff" """)
@click.option('--matplotlib',default=False, required=False, type = bool, help = "Whether to use matplotlib to render the image, if True, need matplotlib installed to use this option. Matplotlib will enable the colorbar, but it can't use spread function")

def points(data_path, x, y, w=600, h=600, x_range=None, y_range=None, 
           agg=None, agg_col =None, by=None, spread_px=None,how=None,
           cmap="fire", background = None,output_apth=None, geo=False, matplotlib=False):
    """Visualize points data.
    
    """

    # add more data format support
    
    # load data
    t1 = datetime.datetime.now()
    if geo:
        import geopandas as gpd
        if data_path.endswith('.parquet'):
            df = gpd.read_parquet(data_path)
        else:
            df = gpd.read_file(data_path)
        # check if df is projected, if not, project it
        if df.crs is not None:
            if not df.crs.is_projected:
                df = df.to_crs(epsg=3857)
        
        df[x] = df.geometry.x
        df[y] = df.geometry.y
    else:
        import pandas as pd
        if data_path.endswith('.csv'):
            df = pd.read_csv(data_path)
        elif data_path.endswith('.parquet'):
            df = pd.read_parquet(data_path)
        elif data_path.endswith('.feather'):
            df = pd.read_feather(data_path)
        elif data_path.endswith('.hdf'):
            df = pd.read_hdf(data_path)
        else:
            raise ValueError('Unsupported data format')

    t2 = datetime.datetime.now()
    print("Time to load data: ", t2-t1)
    # if w and h are not specified, use the default values
    t3 = datetime.datetime.now()
    if x_range:
        x_range = tuple(map(float, x_range.split(',')))
    if y_range:
        y_range = tuple(map(float, y_range.split(',')))

    # projection
    cas_keywords = {
        "plot_width":w,
        "plot_height":h,
        "x_range":x_range,
        "y_range":y_range,
        "x_axis_type":'linear',
        "y_axis_type":'linear',
    }
    import datashader as ds
    import datashader.transfer_functions as tf

    canvas = ds.Canvas(**cas_keywords)

    t4 = datetime.datetime.now()
    print("Time to create canvas: ", t4-t3)
    t5 = datetime.datetime.now()
    # aggregation
    agg_keywords ={
        "source":df,
        "x":x, 
        "y":y,
        "agg":ds.count()

    }

    if agg:
        agg = getattr(ds, agg)
        agg_keywords["agg"] = agg()

    if agg_col:
        agg_keywords["agg"] = agg(agg_col)
        
    
    if by:
        # convert to categorical
        df[by] = df[by].astype('category')
        agg_keywords["source"] = df
        agg_keywords["agg"] = ds.by(by, agg_keywords["agg"])


    if matplotlib:
        import matplotlib.pyplot as plt
        from datashader.mpl_ext import dsshow, alpha_colormap

        fig, ax = plt.subplots()
        artist0 = dsshow(df, ds.Point(x, y), aggregator = agg_keywords["agg"], 
                         x_range=x_range, y_range=y_range,
                         cmap= cc.palette[cmap], aspect='equal', 

                         plot_width=w, plot_height=h,
                         ax=ax)
        plt.colorbar(artist0, ax=ax)

        if background:
            ax.set_facecolor(background)
        plt.savefig(output_apth)
    # arctist = dsshow( df, agg=aggc, cmap=cc.palette[cmap], how=how)
    # plt.colorbar(arctist)
    # plt.show()
    # background
    else:

    #  agggregation
        aggc = canvas.points(**agg_keywords)
        # spread
        if spread_px:
            aggc = tf.spread(aggc, px = spread_px)
        # shade
        shade_keywords = {
            "agg":aggc,
            "cmap":cc.palette[cmap],
            "how":how,
        }

        
        img = tf.shade(**shade_keywords)

        if background:
            
            img = tf.set_background(img, background)
        

        # save to file
        img.to_pil().save(output_apth)
    t6 = datetime.datetime.now()
    print("Time to create image: ", t6-t5)
    print("Total time: ", t6-t1)


import datashader as ds
import datashader.transfer_functions as tf


def nodesplot(nodes, name=None, canvas=None, cat=None, cvsopts=None):
    canvas = ds.Canvas(**cvsopts) if canvas is None else canvas
    aggregator=None if cat is None else ds.count_cat(cat)
    agg=canvas.points(nodes,'x','y',aggregator)
    return tf.spread(tf.shade(agg, cmap=["#FF3333"]), px=1, name=name)

def edgesplot(edges, name=None, canvas=None, cvsopts=None, edge_cmap=None):
    canvas = ds.Canvas(**cvsopts) if canvas is None else canvas

    if edge_cmap:
        return tf.shade(canvas.line(edges, 'x','y', agg=ds.count()), cmap=cc.palette[edge_cmap], name=name)
    return tf.shade(canvas.line(edges, 'x','y', agg=ds.count()), name=name)
    
def graphplot(nodes, edges, name="", canvas=None, cat=None, cvsopts=None, edge_cmap=None):
    if canvas is None:
        xr = nodes.x.min(), nodes.x.max()
        yr = nodes.y.min(), nodes.y.max()
        canvas = ds.Canvas(x_range=xr, y_range=yr, **cvsopts)
        
    np = nodesplot(nodes, name + " nodes", canvas, cat, cvsopts)
    ep = edgesplot(edges, name + " edges", canvas, cvsopts, edge_cmap)
    return tf.stack(ep, np, how="over", name=name)


@click.command()
@click.argument('nodes_file', type=click.Path(exists=True), required=True)
@click.argument('edges_file', type=click.Path(exists=True), required=True)
@click.argument('output_path',default = None, type = str, required=True)

@click.option('--w', default=600,type = int, required=False, help = 'How many pixels wide to make the image')
@click.option('--h', default=600, type = int,required=False, help = 'How many pixels high to make the image')
@click.option('--x',default='x',type= str, required=False, help = """Column name for x coordinates, e.g. "x", if use layout="geo", x is required """)
@click.option('--y',default='y',type= str, required=False, help = """Column name for y coordinates, e.g. "y", if use layout="geo", y is required """)
@click.option('--source',default='source',type= str, required=False, help = """Column name for source node, e.g. "source" """)
@click.option('--target',default='target',type= str, required=False, help = """Column name for target node, e.g. "target" """)
@click.option('--id',default=None,type= str, required=False, help = """Column name for node id, e.g. "id" """)
@click.option('--layout',default='random',type= str, required=False, help = """Layout algorithm, e.g. "random", "forceatlas2", "geo" """)
@click.option('--cat',default=None, type = str, required=False, help = """Column to group by, e.g. "category", see datashader docs (https://datashader.org/api.html#reductions) for more options""")
@click.option('--background',default=None, required=False, type = str, help = """Background color, e.g. "black", "white", "#000000", "#ffffff" """)
@click.option('--bundle',default=False, required=False, type = bool, help = """Whether to bundle the edges""")
@click.option('--bw', default=None,type = float, required=False, help = 'initial_bandwidth for bundling')
@click.option('--decay', default=None, type = float, required=False, help = 'decay for bundling')
@click.option('--edge_cmap',default= None, required=False, type = str, help = 'Name of the colormap for edges, see https://colorcet.holoviz.org for more options')
def network(nodes_file, edges_file, output_path, w=600, h=600, x="x",y="y", source="source", target="target", id=None,
            layout="forceatlas2",cat=None, 
            background="white", bundle=False, bw=None, decay=None, edge_cmap=None):

    # read data
    import pandas as pd
    from datashader.layout import random_layout, circular_layout, forceatlas2_layout
    from datashader.bundling import connect_edges, hammer_bundle

    if nodes_file.endswith('.parquet'):
        cnodes = pd.read_parquet(nodes_file)
    elif nodes_file.endswith('.csv'):
        cnodes = pd.read_csv(nodes_file)
    else:
        raise ValueError('Unsupported data format')
    
    cnodes = cnodes.rename(columns={x:"x", y:"y"})


        
    # cnodes.drop(columns=['AirportID'], inplace=True)
    # this script can't handle id 

    if edges_file.endswith('.parquet'):
        cedges = pd.read_parquet(edges_file)
    elif edges_file.endswith('.csv'):
        cedges = pd.read_csv(edges_file)
    else:
        raise ValueError('Unsupported data format')
    
    cedges = cedges.rename(columns={source:"source", target:"target"})

    if id:
        cnodes["order"] = range(len(cnodes))
        mapper = cnodes.set_index(id)["order"].to_dict()
        cedges["source"] = cedges["source"].map(mapper)
        cedges["target"] = cedges["target"].map(mapper)
    # print(cedges.head())
    # layout
    layouts = {
        "random":random_layout,
        "circular":circular_layout,
        "forceatlas2":forceatlas2_layout
    }
    
    if layout == "geo":
        layout = cnodes.rename(columns={x:"x", y:"y"})
        # print(layout.head())
    else:

        layout = layouts[layout](cnodes, cedges)
        print(layout.head())

    cvsopts = dict(plot_height=h, plot_width=w)
    if bundle:
        bundle_keywords = {
            }
        if bw:
            bundle_keywords["initial_bandwidth"] = bw
        if decay:
            bundle_keywords["decay"] = decay        
        plot = graphplot(layout, hammer_bundle(layout,cedges, **bundle_keywords), "title",  cat=cat, cvsopts=cvsopts, edge_cmap=edge_cmap)

    else:
        plot = graphplot(layout, connect_edges(layout,cedges), "title",  cat=cat, cvsopts=cvsopts, edge_cmap=edge_cmap)
    img = tf.set_background(plot, background)
    img.to_pil().save(output_path)



main.add_command(points)
main.add_command(network)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
