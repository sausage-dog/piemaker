import tkinter.filedialog
import tkinter as tk
import etf_pie_maker
import produce_spreadsheet
from pprint import pprint
import inspect
from sys import platform

class Setting():
    def __init__(self):

        self.split_between_pies = [1]
        self.remove_below_half_percent = [False]
        self.only_212_frac = [False]
        self.only_ISA_212_frac = [False]
        self.os = [None]
        self.error_string = [""]

        if platform == "linux" or platform == "linux2":            
            self.os[0] = 0
        elif platform == "darwin":            
            self.os[0] = 1
        elif platform == "win32":            
            self.os[0] = 2     

        self.etf_locations = []
        self.user_securities = []         ## security, ticker, weight, post/pre


class MainApp(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        ## instance of settings
        setting = Setting()
        
        ## user communication
        self.err_lab = ErrorLabel(self)
        self.err_lab.grid(row=2, column=0)
                
        self_title = tk.Label(self, text="ETF blender",anchor='w', font='Helvetica 18 bold')
        self_title.grid(row=0, column=0, sticky="nsew", pady=(0,20))

        self.adding_files_interface = AddExelFiles(self, setting, self.err_lab)
        self.adding_files_interface.grid(row=1, column=1)

        self.user_sec = SecurityHolder(self, setting, self.err_lab)
        self.user_sec.grid(row=1, column=0, sticky="nsew")

        self.frame_canvas = tk.Frame(self)
        self.frame_canvas.grid(row=2, column=1, sticky="nsew",padx=(20,20),pady=(20,20))

        self.toggle_board = SettingsSwitchBoard(self.frame_canvas,setting,self.err_lab)
        self.toggle_board.pack(side='left')        

        self.make_pie_but = MakeNewPie(self.frame_canvas, setting, self.err_lab)
        self.make_pie_but.pack(side='right')
  

class ErrorLabel(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        self.error_info = tk.Label(self)
        self.error_info.pack()      

    def DisplayError(self, error_string, err=False):
        
        if err is True:
            self.error_info.config(fg='red',text=error_string)
        else:
            self.error_info.config(fg='black',text=error_string)


class SearchFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        self.label = tk.Label(self, text="this is SearchFrame")
        self.label.pack()

        master.label1 = MainApp.create_labels(self, master)
        master.label1.grid()


class MakeNewPie(tk.Frame):
    def __init__(self, master, setting, err_disp):
        super().__init__(master)

        self.local_setting = setting
        self.err_disp = err_disp

        self.make_pie_button = tk.Button(self, text="Make PIE", command=self.RunPieMaker, width=10)
        self.make_pie_button.pack()

        self.pies = None
        self.failed_add = None

    def RunPieMaker(self):       

        ## make new window to display
        self.pies, self.failed_add = etf_pie_maker.ExternalMain(self.local_setting)    

        if len(self.pies) > 0:

            window = tk.Toplevel(self)       
            
            self.pie_sets = []

            self.frame_canvas = tk.Frame(window)
            self.frame_canvas.pack()

            if len(self.failed_add) > 0:
                failure_string = "Failed to add due to rounding: "
                for failure in self.failed_add:
                    failure_string = failure_string + str(failure[0]) + ' '

                self.fails = tk.Label(window,text=failure_string,font=('Helvetica', 15, 'bold')).pack(side='top')

            grid_pos = [[1,0],[1,1],[2,0],[2,1]]

            for ids, pie in enumerate(self.pies):
                self.pie_sets.append(PieDisplay(self.frame_canvas,pie,ids, len(self.pies)).grid(row = grid_pos[ids][0], column = grid_pos[ids][1],padx=20, pady=20))


            if len(self.pie_sets) == 1:
                self.err_disp.DisplayError("Made new ETF across 1 pie")
            else:
                self.err_disp.DisplayError("Made new ETF split across " + str(len(self.pie_sets)) + " pies")

            ## button to turn into an excell
            self.make_exell = tk.Button(window,text='Make Exell', command=self.CallProduceSpreadsheet).pack(side='bottom', pady=(20,20))

        else:
            self.err_disp.DisplayError(self.local_setting.error_string[0])    

    def CallProduceSpreadsheet(self):
        produce_spreadsheet.ProduceSpreadsheet(self.local_setting, self.pies, self.failed_add)



class PieDisplay(tk.Frame):
    def __init__(self, master, pie_obj, pie_number, scaling_factor):
        super().__init__(master)

        ## label with pie number
        self.pie_indx = tk.Label(self, font=('Helvetica', 15, 'bold'), text="Pie["+str(pie_number+1)+"] securities: "+str(pie_obj.number_of_securities[0])+" total weight: "+str(pie_obj.sum_of_security_weighing[0]))
        self.pie_indx.pack(side='top')

        self.frame_canvas = tk.Frame(self)
        self.frame_canvas.pack()

        # Add a canvas in that frame
        self.canvas = tk.Canvas(self.frame_canvas, width=200)        
        self.canvas.pack(side='left')

        # # Link a scrollbar to the canvas
        self.vsb = tk.Scrollbar(self.frame_canvas, orient="vertical", command=self.canvas.yview)
        self.vsb.pack(side='right', fill='y')
        self.canvas.configure(yscrollcommand=self.vsb.set)

        # Create a frame to contain the buttons
        self.frame_buttons = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame_buttons, anchor='nw')

        ## list of pies with indeces
        self.entries = []        

        sum_pie = 0

        for sec in reversed(pie_obj.securities):
            self.entries.append(SecDisplay(self.frame_buttons, sec[0], sec[1], scaling_factor).pack(side='bottom'))
            sum_pie = sum_pie + sec[1]        

        self.frame_canvas.config(height=5, width=5)
        self.frame_buttons.update_idletasks()

        # Set the canvas scrolling region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))  

        self.left_over_lbl = tk.Label(self,anchor="e", font=('Helvetica', 15, 'bold'), text="Leftover: "+str(float(100 - sum_pie*scaling_factor)))
        self.left_over_lbl.pack(side='bottom')       


class SecDisplay(tk.Frame):
    def __init__(self, master, sec_name, sec_weight, scaling_factor):
        super().__init__(master)

        ## security name
        self.sec_name = tk.Label(self, text=str(sec_name),width=10, anchor="e")
        self.sec_name.pack(side='left')

        ## security name
        self.sep = tk.Label(self, text=":",width=3)
        self.sep.pack(side='left')        

        ## security name
        self.sec_weight = tk.Label(self, text=str(float(sec_weight*scaling_factor)), width=5)
        self.sec_weight.pack(side='left')


class AddExelFiles(tk.Frame):
    def __init__(self, master,settings, err_disp):
        super().__init__(master)

        self.settings = settings
        self.err_disp = err_disp

        self.sub_frame = tk.Frame(self)
        self.sub_frame.pack()       

        self.add_label = tk.Label(self.sub_frame,text="Select ETF excel files ")
        self.add_label.pack(side='left')

        ## add input bottun
        self.add_excels_button = tk.Button(self.sub_frame, text="Add files",command=self.GetFiles)
        self.add_excels_button.pack(side='left')

        ##
        self.etf_holder = ETFHolder(self,settings, err_disp)
        self.etf_holder.pack(side='bottom')           

    def GetFiles(self):

        new_files = 0 
        separator = ''

        if self.settings.os[0] == 2:
            separator = '\\'
        else:
            separator = '/'

        self.filenames = tkinter.filedialog.askopenfilenames(initialdir=separator,title="search ETFs", filetypes=[("Excel files", ".xlsx .xls")])        

        ## add to settings
        if len(self.filenames) > 0:
            for file_name in self.filenames:

                ## filter to see if not present already
                if file_name not in [row[1] for row in self.settings.etf_locations]:

                    ## make shortened version
                    shortened = file_name[file_name.rfind(separator)+1:]               

                    ## load file
                    all_ = [shortened, file_name, 1]
                    self.settings.etf_locations.append(all_)
                    new_files = new_files + 1

            ## pass files to be added
            self.etf_holder.AddEntities([row[0] for row in self.settings.etf_locations])
   

class SettingsSwitchBoard(tk.Frame):
    def __init__(self, master, settings, err_disp):
        super().__init__(master)

        self.local_settings = settings
        self.err_disp = err_disp

        ## ability to spread designed ETF over multiple pies
        self.togle_split_pies = MultOptionToggle(self, "Split between multiple pies",settings.split_between_pies, 4)
        self.togle_split_pies.grid(row=1, column=0, sticky="nsew")

         ## remove stuff that isn't available as ISA
        self.only_frac = Toggle(self, "Only fractional securities on T212",settings.only_212_frac)
        self.only_frac.grid(row=2, column=0, sticky="nsew")

        ## remove stuff that isn't available as T212 frac
        self.only_ISA_frac = Toggle(self, "Only fractional ISA securities on T212",settings.only_ISA_212_frac)
        self.only_ISA_frac.grid(row=3, column=0, sticky="nsew")
 
        ## Cut off at securities above 50
        self.togle_whatvs = Toggle(self, "Remove security weightings below 0.5%",settings.remove_below_half_percent)
        self.togle_whatvs.grid(row=4, column=0, sticky="nsew")


class MultOptionToggle(tk.Frame):
    def __init__(self, master, switch_label,exact_setting, number_of_states):
        super().__init__(master)
        self.local_exact_setting = exact_setting
        self.number_of_states = number_of_states
        self.frame = tk.Frame(self)
        self.frame.pack()
        self.current_state = 1

        self.switch_label = tk.Label(self.frame, text = switch_label, width=30, anchor='e')
        self.switch_label.grid(row=0, column=0, columnspan=1, sticky='e')
        
        self.button = tk.Button(self.frame, text='Disabled', command=self.NextState, width=10)
        self.button.grid(row=0, column=1, columnspan=4, sticky='w')
        self.recording = False    

    def NextState(self):

        if self.current_state < self.number_of_states:
            self.current_state = self.current_state + 1
            self.button.config(text = str(self.current_state)+ ' pies')
            
        else:
            self.current_state = 1
            self.button.config(text = 'Disabled')

        self.local_exact_setting[0] = self.current_state

class Toggle(tk.Frame):
    def __init__(self, master, switch_label,exact_setting):
        super().__init__(master)
        self.local_exact_setting = exact_setting

        self.frame = tk.Frame(self)
        self.frame.pack()

        self.switch_label = tk.Label(self.frame, text = switch_label, width=30, anchor='e')
        self.switch_label.grid(row=0, column=0, columnspan=1, sticky='e')
        
        self.button = tk.Button(self.frame, text='Disabled', command=self.clicked, width=10)
        self.button.grid(row=0, column=1, columnspan=4, sticky='w')
        self.recording = False        

    def clicked(self):
        self.recording = not self.recording
        if self.recording:
            self.button.config(text='Enabled')
            self.local_exact_setting[0] = True
        else:
            self.button.config(text='Disabled')
            self.local_exact_setting[0] = False

  
class ETFHolder(tk.Frame):
    def __init__(self, master, settings, err_disp, files = None):
        super().__init__(master)

        self.local_settings = settings
        self.err_disp = err_disp

        self.frame_canvas = tk.Frame(self)
        self.frame_canvas.pack()

        # Add a canvas in that frame
        self.canvas = tk.Canvas(self.frame_canvas, width=500)        
        self.canvas.pack(side='left')

        # # Link a scrollbar to the canvas
        self.vsb = tk.Scrollbar(self.frame_canvas, orient="vertical", command=self.canvas.yview)
        self.vsb.pack(side='right', fill='y')
        self.canvas.configure(yscrollcommand=self.vsb.set)

        # Create a frame to contain the buttons
        self.frame_buttons = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame_buttons, anchor='nw')

        self.entries = []

    def AddEntities(self,files):

        new_files = 0 

        for ETF_name in files:
            if any(obj.ETF_name['text'] == ETF_name for obj in self.frame_buttons.winfo_children()):
                None
            else:
                self.entries.append(ETFEntry(self.frame_buttons, self.local_settings, ETF_name, self.err_disp, command_remove=self.RemoveGivenETF).pack())
                new_files = new_files + 1

        if new_files>1:
            self.err_disp.DisplayError("Added "+str(new_files)+" new files")       
        elif new_files == 1:
            self.err_disp.DisplayError("Added new file")    
        else:
            self.err_disp.DisplayError("No new files added")    

        self.frame_canvas.config(height=5, width=5)
        self.frame_buttons.update_idletasks()

        # Set the canvas scrolling region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))     
        
    def RemoveGivenETF(self,self_pass,etf_name):

        wlist=self.frame_buttons.winfo_children()
        for i,entry in enumerate(wlist):            
            if self_pass is entry:                
                wlist[i].destroy()                

                for etf_name_instance in self.local_settings.etf_locations:
                    if etf_name_instance[0] is etf_name:                        
                        self.local_settings.etf_locations.remove(etf_name_instance)

        self.frame_canvas.config(height=5, width=5)
        self.frame_buttons.update_idletasks()

        # Set the canvas scrolling region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))  


class ETFEntry(tk.Frame):
    def __init__(self, master, settings, ETF_name, err_disp, command_remove=None):
        super().__init__(master) 

        self.local_settings = settings
        self.err_disp = err_disp

        ## strign obtained
        self.ETF_name = tk.Label(self, text = ETF_name, width=25, anchor='w')
        self.ETF_name.pack(side = 'left', padx=(20,0))

        ## custom percentage
        self.ETF_weight = tk.Label(self, text = "weight: 1.0", width=10)
        self.ETF_weight.pack(side = 'left', padx=(2,2))

        ## new weight
        self.new_weight_entry = tk.Entry(self, width=3)
        self.new_weight_entry.pack(side = 'left')

        ## confirm button
        self.confirm_weight = tk.Button(self, text="Update", command=self.UpdateValue, width=6)
        self.confirm_weight.pack(side = 'left')     

        ## remove button           
        self.remove_etf = tk.Button(self, text="Remove", command=lambda: command_remove(self,ETF_name), width=6)
        self.remove_etf.pack(side = 'left')  

    def UpdateValue(self):        

        ## check that within limits
        val = float(self.new_weight_entry.get())      
        if val < 1 and val > 0:
            self.ETF_weight.config(text="weight: "+str(float(val)))

            ## update actual thing
            for etf in self.local_settings.etf_locations:
                if etf[0] == self.ETF_name['text']:
                    etf[2] = val

        elif val > 1:            
            self.err_disp.DisplayError("Weight exceeds 1", True)
        elif val < 0:
            self.err_disp.DisplayError("Weight less than 0", True)

        ## clear window
        self.new_weight_entry.delete(0, tk.END)

class SecurityHolder(tk.Frame):
    def __init__(self, master, settings, err_disp):
        super().__init__(master)
        self.local_settings = settings
        self.err_disp = err_disp

        self.sub_frame = tk.Frame(self)
        self.sub_frame.pack()

        self.label_sec_holder = tk.Label(self.sub_frame,text="Add securities")
        self.label_sec_holder.pack(side="left")

        self.add_sec_entry = tk.Entry(self.sub_frame)
        self.add_sec_entry.pack(side="left")

        self.confirm_button = tk.Button(self.sub_frame,text='confirm',command=self.AddSecurities)
        self.confirm_button.pack(side="left")

        self.frame_canvas = tk.Frame(self)
        self.frame_canvas.pack()

        # Add a canvas in that frame
        self.canvas = tk.Canvas(self.frame_canvas, width=500)        
        self.canvas.pack(side='left')

        self.entries = []

        # Create a frame to contain the buttons
        self.frame_buttons = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame_buttons, anchor='nw')

         # # Link a scrollbar to the canvas
        self.vsb = tk.Scrollbar(self.frame_canvas, orient="vertical", command=self.canvas.yview)
        self.vsb.pack(side='right', fill='y')
        self.canvas.configure(yscrollcommand=self.vsb.set)

    def AddSecurities(self):

        ## read from entry
        entities_string = self.add_sec_entry.get()        
        weight = 0
        new_ents = 0

        if len(entities_string) > 0:

            ## process the string
            entities_no_comma =  entities_string.split(',') ## maytbe change to space       

            ## raise and strip white space
            entities_upper = [sec.upper().strip() for sec in entities_no_comma]

            for rem_sec in entities_upper:                               

                if len(rem_sec) > 0:
                    if ' ' in rem_sec:
                        two_vals = rem_sec.split(' ')                        
                        if len(two_vals) == 2:                        
                            weight = two_vals[1]
                            rem_sec = two_vals[0]

                    else:                        
                        if not rem_sec.isspace() and rem_sec != ' ':
                            weight = 1                            

                    ## filter to see if not present already
                    if rem_sec not in [row[0] for row in self.local_settings.user_securities]:  

                        try:
                            if int(weight) or  float(weight):
                                if float(weight) < 100 and float(weight) > 0:
                                    self.local_settings.user_securities.append([rem_sec,weight,True])
                                    new_ents = new_ents + 1
                        except:
                            None
            ## iterate over existing securities in the settigns
            for sec in self.local_settings.user_securities:
                if any(obj.security_name['text'] == sec[0] for obj in self.frame_buttons.winfo_children()):     
                    None               
                else:
                    self.entries.append(SecurityEntry(self.frame_buttons,sec[0],self.err_disp,self.local_settings,command_remove=self.RemoveGivenSecurity, weight = sec[1] ).pack())
                    if new_ents == 1:
                        self.err_disp.DisplayError('Added custom security')    
                    else:
                        self.err_disp.DisplayError('Added '+str(new_ents)+' custom securities')

        ## remove entries from view
        self.add_sec_entry.delete(0,tk.END)

        self.frame_canvas.config(height=5, width=5)
        self.frame_buttons.update_idletasks()

        # Set the canvas scrolling region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))   
        
    def RemoveGivenSecurity(self,self_pass,security_name):

        wlist=self.frame_buttons.winfo_children()
        for i,entry in enumerate(wlist):            
            if self_pass is entry:                
                
                wlist[i].destroy()                                         

                for sec_name_instance in self.local_settings.user_securities:
                    if sec_name_instance[0] is security_name:                        
                        self.local_settings.user_securities.remove(sec_name_instance)

        self.frame_canvas.config(height=5, width=5)
        self.frame_buttons.update_idletasks()

        # Set the canvas scrolling region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))   


class SecurityEntry(tk.Frame):
    def __init__(self, master, security_name, err_disp, settings, command_remove=None, weight=1):
        super().__init__(master)

        self.sec_frame = tk.Frame(self) 
        self.sec_frame.pack()

        self.err_disp = err_disp
        self.local_settings = settings

        ## strign obtained
        self.security_name = tk.Label(self.sec_frame, text = security_name, width=10, anchor='w')
        self.security_name.pack(side = 'left')

        ## custom weight
        self.security_weight = tk.Label(self.sec_frame, text = ("weight: "+str(float(weight))), width=10, anchor='w')
        self.security_weight.pack(side = 'left', padx=(5, 5), anchor='w')

        ## new weight
        self.new_weight_entry = tk.Entry(self.sec_frame, width=3)
        self.new_weight_entry.pack(side = 'left')

        ## confirm button
        self.confirm_weight = tk.Button(self.sec_frame, text="Update", command=self.UpdateValue, width='6')
        self.confirm_weight.pack(side = 'left')     

        ## weight insertion point
        self.scale_point = tk.Button(self.sec_frame, text="Initial", command=self.UpdateScalingOption, width='6')
        self.scale_point.pack(side='left')
        self.scale_option = True

        ## remove button           
        self.remove_etf = tk.Button(self.sec_frame, text="Remove", command=lambda: command_remove(self,security_name), width='6')
        self.remove_etf.pack(side = 'left') 

    def UpdateScalingOption(self):
        scaling  = None
        self.scale_option = not self.scale_option
        if self.scale_option:
            self.scale_point.config(text='Initial')
            scaling = True
        else:
            self.scale_point.config(text='Final')
            scaling = False

        for user_sec in self.local_settings.user_securities:                        
            if user_sec[0] == self.security_name['text']:
                user_sec[2] = scaling

    def UpdateValue(self):

        numb = None

        try:
            numb = float(self.new_weight_entry.get())

            ## check if an int
            if isinstance(numb,float) or isinstance(numb,int):                       

                if numb > 100:
                    self.err_disp.DisplayError("Weight exceeds 100",True)
                elif numb < 0.5:
                    self.err_disp.DisplayError("Weight below 0.5",True)
                elif (numb*10)%5 !=0:
                    self.err_disp.DisplayError("Weight not a multiple of 0.5",True)
                else:
                    ## update label
                    self.security_weight.config(text="weight: "+str(float(numb)))
                    ## update list
                    for user_sec in self.local_settings.user_securities:                        
                        if user_sec[0] == self.security_name['text']:
                            user_sec[1] = numb

                    ## comunicate update
                    self.err_disp.DisplayError("Updated weight for " + self.security_name['text'])
        except:            
            self.err_disp.DisplayError("Didn't provide a number",True)

        self.new_weight_entry.delete(0, tk.END)


class AddConsole2(tk.Frame):
    def __init__(self, master, entry_label=None):

        super().__init__(master)
        self.top_frame = tk.Frame(self)
        self.bottomframe = tk.Frame(self)        

        self.top_frame.pack()
        self.bottomframe.pack( side = 'bottom')

        ## label for entry
        self.entry_label = tk.Label(self.top_frame, text = entry_label, width=50, anchor='w')
        self.entry_label.pack( side = 'top')

        ## input bar
        self.security_entry = tk.Entry(self.top_frame, fg="blue", width=45)
        self.security_entry.pack( side = 'left')

        ## submit button
        self.submit_button = tk.Button(self.top_frame, text="Submit", fg="green", command=self.submit)
        self.submit_button.pack( side = 'left' )

        ## clear button
        self.clear_button = tk.Button(self.top_frame, text="Clear", fg="blue", command=self.clear)
        self.clear_button.pack( side = 'left' )

    def submit(self):        
        self.added_securities.insert("0.0",self.security_entry.get())
        self.security_entry.delete(0, tk.END)

    def clear(self):
        self.added_securities.delete("1.0", tk.END)


class AddConsole(tk.Frame):
    def __init__(self, master, entry_label=None):

        super().__init__(master)

        self.top_frame = tk.Frame(self)
        self.bottomframe = tk.Frame(self)        

        self.top_frame.pack()
        self.bottomframe.pack( side = 'bottom')

        ## label for entry
        self.entry_label = tk.Label(self.top_frame, text = entry_label, width=50, anchor='w')
        self.entry_label.pack( side = 'top')

        ## input bar
        self.security_entry = tk.Entry(self.top_frame, fg="blue", width=45)
        self.security_entry.pack( side = 'left')

        ## submit button
        self.submit_button = tk.Button(self.top_frame, text="Submit", fg="green", command=self.submit)
        self.submit_button.pack( side = 'left' )

        ## clear button
        self.clear_button = tk.Button(self.top_frame, text="Clear", fg="blue", command=self.clear)
        self.clear_button.pack( side = 'left' )

        self.added_securities = tk.Text(self.bottomframe, fg="black", height=10)
        self.added_securities.pack( side = 'bottom',fill=tk.BOTH)

    def submit(self):        
        self.added_securities.insert("0.0",self.security_entry.get())
        self.security_entry.delete(0, tk.END)

    def clear(self):
        self.added_securities.delete("1.0", tk.END)

def main():

    root = tk.Tk()
    mainAppObject = MainApp(root)
    mainAppObject.pack(padx=20, pady=20)
    root.mainloop()


if __name__ == "__main__":
    main()









