"""Console script for datashader_cli."""

import click
import datetime
import colorcet as cc
import sys


@click.group()
def main(args=None):
    """Quick visualization of large datasets using CLI based on datashader.
    
    Supported data format: csv, parquet, hdf, feather, geoparquet, shapefile, geojson, geopackage, etc.
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
main.add_command(points)




if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
