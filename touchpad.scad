/* --COPYRIGHT--,BSD
 * Copyright (c) 2019, Texas Instruments Incorporated
 * Copyright (c) 2025, Diodes Delight
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * *  Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 *
 * *  Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * *  Neither the name of Texas Instruments Incorporated nor the names of
 *    its contributors may be used to endorse or promote products derived
 *    from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
 * THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
 * OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
 * OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
 * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 * --/COPYRIGHT--*/
//============================================================================
// touchpad.scad
//
// This OpenScad script creates a diamond matrix for capacitive touchpad sensors.
// Shape options are Square, Circle and Custom. The sensor design is exported
// to DXF and can then be imported into any PCB layout.
// User controls sensor design by editing various parameters, such as size,
// number of elements, spacing, etc. OpenSCAD is unit less so the values you use
// to represent your dimensions can be mm, mils, etc.  Just remember
// when importing into PCB CAD tool, specify same units used in the design.
// For example, if parameters are in mm, then specify mm when importing.
//
// NOTE:  The accuracy of the dimensions created by this script cannot be
// guaranteed.  A reasonable effort has been made verify the accuracy,
// however, it is up to the user to verify.
// 
// Texas Instruments
// MSP430 Applications
// version 1.0
// February 13, 2020

// ================= CONSTANTS ======================
// DON'T CHANGE THESE 
$fn = 400;      // Defines number of fragments
$circle = 0;    // Defines for shapes
$square = 1;
$custom = 2;
$none = 3;      // No shape shows entire diamond matrix (development purposes)
$x_max = 30;     // Maximum number or supported columns + 1
$y_max = 30;     // Maximum number of supported rows + 1

//================== USER INPUTS ====================
// #1 - SPECIFY IF ROUND OR SQUARE OR CUSTOM
shape = 1; 

// #2 - SPECIFY THE NUMBER OF RX AND TX
rows = 20;
columns = 14;

// #3 - SPECIFY THE WIDTH AND HEIGHT OF THE TOUCHPAD IN UNITS
//      IF CIRCLE, WIDTH AND HEIGHT SHOULD BE SET EQUAL
//      IF CUSTOM, REFER TO DXF OUTPUT
touchpad_width = 53;
touchpad_height = 74;

// #4 - SPECIFY THE EDGE TO EDGE SPACING BETWEEN DIAMONDS
diamond_spacing = .15;

// #5 - SPECIFY DXF FILE TO IMPORT
dxf = "custom-outline.dxf";  // example file (20mm x 14mm ellipse)

// #6 - (OPTIONAL FOR CUSTOM) SPECIFY OBJECT ROTATION (DEGREES)
sensor_rotation = 90;

//================= CALCULATIONS ====================
tip2tip_spacing_x = (diamond_spacing * 1.414);
tip2tip_spacing_y = (diamond_spacing * 1.414);
pitch_x = (touchpad_width / columns);
pitch_y = (touchpad_height/ rows);
diamond_x_size = pitch_x - tip2tip_spacing_x;
diamond_y_size = pitch_y - tip2tip_spacing_y;
touchpad_x_center = touchpad_width/2;
touchpad_y_center = touchpad_height/2;

//=================== MODULE ===========================
module generate_diamonds()
{
    for(i=[0:1:$y_max-1])
        translate([0,(i * pitch_y)+tip2tip_spacing_y/2, 0]){
            for(i=[0:1:$x_max-1])
            translate([(i * pitch_x)+tip2tip_spacing_x/2, 0, 0])
                polygon(points = [[0,diamond_y_size/2],[diamond_x_size/2, diamond_y_size ],[diamond_x_size, diamond_y_size/2],[diamond_x_size/2,0]], paths = [[0,1,2,3]]);
        }
}

//================= MAIN CODE ===========================
// Rotate Final sensor
rotate([0,0,sensor_rotation])
{
    translate([touchpad_width/2,-touchpad_height/2,0]){

        // Intersection of diamond matrix and bounding object (shape)
        intersection()
        {
           // Center the resulting sensor pattern
           translate([-touchpad_width/2, -touchpad_height/2,0])
           {
                // Combine 2 diamond patterns
                union()
                {
                   translate([-pitch_x/2,0,0])
                   {
                       // Draw second set of diamonds
                       translate([pitch_x/2,-pitch_y/2,0])
                           generate_diamonds();
                       // Draw first set of diamonds
                       translate([0,0,0])
                           generate_diamonds();
                    }
                }//end union

            } 
            // Create the bounding object shape.
            if(shape == $circle)
            {   
                 circle(d=touchpad_width);  
            }
            else if(shape == $square)
            {
                square([touchpad_width, touchpad_height],center = true);
            }
            else if(shape == $custom)
            {
                    // option to scale the DXF
                    //scale([1,1,0])
                    import(dxf, convexity = 3);
            }
            
        }// end intersection
    }
}
// GENERATE REPORT FOR DEBUGGING
echo("BEGIN REPORT");
echo("shape = ", shape);
echo("diamond_x = ", diamond_x_size);
echo("diamond_y = ",diamond_y_size);
echo("tip-tip spacing (adjacent diamonds) = ", tip2tip_spacing_x);
echo("pitch_x = ",pitch_x);
echo("pitch_y = ",pitch_y);
echo("sensor_rotation(deg) = ", sensor_rotation);
echo("END REPORT");




