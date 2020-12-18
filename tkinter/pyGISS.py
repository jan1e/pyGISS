import tkinter as tk
from tkinter import filedialog
import pyproj
import shapefile
import shapely.geometry


class Map(tk.Canvas):

    projections = {
        'mercator': pyproj.Proj(init="epsg:3395"),
        'spherical': pyproj.Proj('+proj=ortho +lon_0=28 +lat_0=47')
        }

    def __init__(self, root):
        super().__init__(root, bg='white', width=1300, height=800)
        self.proj = 'mercator'
        self.ratio, self.offset = 1, (0, 0)
        self.bind('<ButtonPress-1>', self.print_coords)
        self.bind('<MouseWheel>', self.zoomer)
        self.bind('<Button-4>', lambda e: self.zoomer(e, 1.3))
        self.bind('<Button-5>', lambda e: self.zoomer(e, 0.7))
        self.bind('<ButtonPress-3>', lambda e: self.scan_mark(e.x, e.y))
        self.bind('<B3-Motion>', lambda e: self.scan_dragto(e.x, e.y, gain=1))
        menu = tk.Menu(root)
        menu.add_command(label="Import shapefile", command=self.import_map)
        menu.add_command(label="Switch projection", command=self.switch_proj)
        menu.add_command(label="test linestring", command=self.import_geodata)
        menu.add_command(label="test points", command=self.import_geopoints)


        root.config(menu=menu)
        self.pack(fill='both', expand=1)

    def to_canvas_coordinates(self, longitude, latitude):
        px, py = self.projections[self.proj](longitude, latitude)
        return px*self.ratio + self.offset[0], -py*self.ratio + self.offset[1]

    def to_geographical_coordinates(self, x, y):
        px, py = (x - self.offset[0])/self.ratio, (self.offset[1] - y)/self.ratio
        return self.projections[self.proj](px, py, inverse=True)

    def import_map(self):
        self.filepath, = filedialog.askopenfilenames(title='Import shapefile')
        self.draw_map()
        #self.create_line(10,10,20,20)
    def import_geodata(self):
        self.filepath, = filedialog.askopenfilenames(title='Import shapefile')
        self.draw_rivers()
    def import_geopoints(self):
        self.filepath, = filedialog.askopenfilenames(title='Import shapefile')
        self.draw_cities()


    def draw_cities(self):
        self.delete('city')
        sf = shapefile.Reader(self.filepath)
        points = sf.shapes()
        for point in points:
            point = shapely.geometry.shape(point)
            if point.geom_type == 'Point':
                point = [point]

            for city in point:
                x1 = self.to_canvas_coordinates(city.coords.xy[0][0], city.coords.xy[1][0])[0] +2
                y1 = self.to_canvas_coordinates(city.coords.xy[0][0], city.coords.xy[1][0])[1] +2
                x2 = self.to_canvas_coordinates(city.coords.xy[0][0], city.coords.xy[1][0])[0] -2
                y2 = self.to_canvas_coordinates(city.coords.xy[0][0], city.coords.xy[1][0])[1] -2


                self.create_oval(x1,y1,x2,y2,
                    fill='black',
                    outline='black',
                    tags=('city',)
                    )

    def draw_map(self):
       
        self.delete('land', 'water')
        self.draw_water()
        sf = shapefile.Reader(self.filepath)
        polygons = sf.shapes()
        for polygon in polygons:
            # convert shapefile geometries into shapely geometries
            # to extract the polygons of a multipolygon
            polygon = shapely.geometry.shape(polygon)
            if polygon.geom_type == 'Polygon':
                polygon = [polygon]
            for land in polygon:
                self.create_polygon(
                    sum((self.to_canvas_coordinates(*c) for c in land.exterior.coords), ()),
                    fill='green3',
                    outline='black',
                    tags=('land',)
                )
           
    # ab hier neuer code
    def draw_rivers(self):

         self.delete('river')
         sf = shapefile.Reader(self.filepath)
         polylines = sf.shapes()
         i=0
         
         for polyline in polylines:
            i= i+1
           
            try:
                polyline = shapely.geometry.shape(polyline)
            except:
                print("Fehler: ein Fluss konnte nicht geladen werden",i)
                continue
                
            #print(polyline.geom_type)    
            if polyline.geom_type == "LineString":
                
                polyline = [polyline]
                for river in polyline:
                    self.create_line(
                        sum((self.to_canvas_coordinates(*c) for c in river.coords), ()),
                        fill='blue3',
                        #outline='black',
                        tags=('river',)                        
                    )
                    #print(i)
            elif polyline.geom_type == "MultiLineString":
                print("multilinestring")
                mls = [polyline]
                for mlsriver in mls:
                    for mlsline in mlsriver:
                        self.create_line(
                            sum((self.to_canvas_coordinates(*c) for c in mlsline.coords), ()),
                            fill='red',
                            #outline='black',
                            tags=('river',)                        
                        )




            
    def draw_water(self):
        if self.proj == 'mercator':
            x0, y0 = self.to_canvas_coordinates(-180, 84)
            x1, y1 = self.to_canvas_coordinates(180, -84)
            self.water_id = self.create_rectangle(
                x1, y1, x0, y0,
                outline='black',
                fill='deep sky blue',
                tags=('water',)
            )
        else:
            cx, cy = self.to_canvas_coordinates(28, 47)
            R = 6371000*self.ratio
            self.water_id = self.create_oval(
                cx - R, cy - R, cx + R, cy + R,
                outline='black',
                fill='deep sky blue',
                tags=('water',)
            )

    def switch_proj(self):
        self.proj = 'mercator' if self.proj == 'spherical' else 'spherical'
        self.draw_map()

    def print_coords(self, event):
        event.x, event.y = self.canvasx(event.x), self.canvasy(event.y)
        print(*self.to_geographical_coordinates(event.x, event.y))

    def zoomer(self, event, factor=None):
        if not factor:
            factor = 1.3 if event.delta > 0 else 0.7
        event.x, event.y = self.canvasx(event.x), self.canvasy(event.y)
        self.scale('all', event.x, event.y, factor, factor)
        self.configure(scrollregion=self.bbox('all'))
        self.ratio *= float(factor)
        self.offset = (
            self.offset[0]*factor + event.x*(1 - factor),
            self.offset[1]*factor + event.y*(1 - factor)
        )


if str.__eq__(__name__, '__main__'):
    root_window = tk.Tk()
    root_window.title('PyGISS: A GIS software in less than 100 lines of Python')
    py_GISS = Map(root_window)
    root_window.mainloop()
