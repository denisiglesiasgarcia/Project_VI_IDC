import pandas as pd
import matplotlib.pyplot as plt
from pathlib import PureWindowsPath
import numpy as np
import seaborn as sns
from datetime import datetime
import os
from datetime import date

def performance_par_site(df, site):
    now = datetime.now()
    date_png = str(now.strftime("%Y-%m-%d"))
    date_titre = str(now.strftime("%d-%m-%Y"))
    # Create a new directory with the current date as its name
    today = date.today()
    directory = os.path.join('01_graphiques\\01_performance_par_site\\', today.strftime("%Y-%m-%d"))
    if not os.path.exists(directory):
        os.makedirs(directory)

    df_analyse_bars = df[['Nom_projet','statut',
                         'Ef,avant,corr (IDC_avant) [MJ/m²]',
                         'Ef,obj*fp (Objectif en EF pondérée après) [MJ/m²]',
                         'Ef,après,corr*fp (Conso. mesurée après) [MJ/m²]',
                         'Part atteinte des objectifs [%]']].copy()
    df_analyse_bars['Baisse IDC visée'] = df_analyse_bars.loc[:, 'Ef,avant,corr (IDC_avant) [MJ/m²]'] - \
                                            df_analyse_bars.loc[:, 'Ef,obj*fp (Objectif en EF pondérée après) [MJ/m²]']
    df_analyse_bars['Baisse IDC réalisée'] = df_analyse_bars.loc[:, 'Ef,avant,corr (IDC_avant) [MJ/m²]'] - \
                                                df_analyse_bars.loc[:, 'Ef,après,corr*fp (Conso. mesurée après) [MJ/m²]']

    df_analyse_bars.rename(columns={'Ef,avant,corr (IDC_avant) [MJ/m²]': 'IDC moy 3 ans avant\n$IDC_{moy3ans}$',
                                    'Ef,obj*fp (Objectif en EF pondérée après) [MJ/m²]': 'Objectif\n$E_{f,obj}*f_{p}$',
                                    'Ef,après,corr*fp (Conso. mesurée après) [MJ/m²]': 'Conso mesurée après\n$E_{f,après,corr}*f_{p}$'
                                    },
                                    inplace=True)
    df_analyse_bars.fillna(0, inplace=True)

    #sauvegarde_png = PureWindowsPath (r"01_graphiques\\01_performance_par_site\\03_bars_par_site_" + site + '-' + date_png + '.png')
    sauvegarde_png = os.path.join(directory, "01_performance_par_site_" + site + '-' + date_png + '.png')

    # filtrer les données selon besoins
    bar_data = df_analyse_bars[df_analyse_bars['Nom_projet'] == site]
    bar_data = bar_data.drop(columns=['statut'])

    # stack pour adapter les données pour le graphique
    # https://stackoverflow.com/questions/66998010/how-to-pivot-from-columns-to-rows-in-pandas
    bar_data = bar_data.set_index (['Nom_projet'])
    bar_data = bar_data.stack().rename_axis (['Nom_projet','Type']).reset_index()
    bar_data.rename(columns={0: 'Valeur'},inplace=True)

    # Séparer les données pour le graphique
    bar_data1 = bar_data[(bar_data['Type'] != 'Part atteinte des objectifs [%]')]
    bar_data1 = bar_data1[(bar_data1['Type'] != 'Baisse IDC réalisée')]
    bar_data1 = bar_data1[(bar_data1['Type'] != 'Baisse IDC visée')]

    bar_data2 = bar_data[(bar_data['Type'] == 'Part atteinte des objectifs [%]')]

    # https://stackoverflow.com/questions/21923524/extracting-single-value-from-column-in-pandas
    perf_atteinte = bar_data2['Valeur'].values[bar_data2['Type'] == 'Part atteinte des objectifs [%]']
    perf_atteinte = int(perf_atteinte * 100)

    bar_data.sort_values (by=['Type'])
    # taille graphique 16/9 avec les bords adapté page word paysage
    
    # Générer histogramme. taillebin est utilisé pour uniformiser le format de l'histogramme et que les axes
    # correspondent bien à la largeur des barres (bin)
    cm = 1 / 2.54
    sns.set (style='white',rc={"figure.figsize":(30* cm, 14.2 * cm)})
    # ax1 = sns.catplot(x='Nom_projet', y='Valeur', hue='Type', kind='bar', data=bar_data1)
    
    ax = sns.barplot (y="Valeur",
                      x="Type",
                      data=bar_data1,
                      order=['IDC moy 3 ans avant\n$IDC_{moy3ans}$',"Objectif\n$E_{f,obj}*f_{p}$",'Conso mesurée après\n$E_{f,après,corr}*f_{p}$'],
                      palette="pastel",
                      legend=False)

    sns.despine()

    ax.bar_label (ax.containers[0])

    height_line85 = bar_data['Valeur'][0] - bar_data['Valeur'][4]*0.85
    text_line85 = '$(E_{f,après,corr}*f_{p})_{max→subv.}=$' + '$' + str(np.round(bar_data['Valeur'][0] - bar_data['Valeur'][4]*0.85, 1)) + ' {MJ/m}^2$'
    ax.axhline (height_line85, xmin=0.445, xmax=0.98, color='indigo', linestyle=(0, (5, 10)), linewidth=0.7)
    # Add text near the line.
    offset_85 = 1
    ax.annotate(text_line85, xy=(2, height_line85 + offset_85), xytext=(1.57, height_line85 + offset_85),
                horizontalalignment='right', verticalalignment='bottom', fontsize=10, color='indigo')

    ####################

    # première flèche
    # find the height of the first and third bars
    first_bar_height = bar_data['Valeur'][bar_data['Type'] == 'IDC moy 3 ans avant\n$IDC_{moy3ans}$'].values[0]
    second_bar_height = bar_data['Valeur'][bar_data['Type'] == 'Objectif\n$E_{f,obj}*f_{p}$'].values[0]
    # set the x-coordinate for the third bar
    x_coord_second_bar = 0.8  # this depends on the actual x-coordinate of the third bar
    # text for the arrow
    text_arrow_baisse_realisee = "Baisse\nobjectif\n"+str('{:.1f}'.format(bar_data['Valeur'][4])) + " MJ/m²"
    # add text at the midpoint of the arrow
    midpoint_height = (first_bar_height + second_bar_height) / 2
    # plot the line (arrow without arrowheads)
    ax.annotate("", xy=(x_coord_second_bar, second_bar_height), xytext=(x_coord_second_bar, first_bar_height),
                arrowprops=dict(arrowstyle="<->", color='moccasin', lw=3))  # increase lw for a thicker line
    # add the text over the line and centered
    u = ax.text(x_coord_second_bar, midpoint_height, text_arrow_baisse_realisee, ha='center', va='center', rotation=0,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="white", lw=2))

    # deuxième flèche
    # find the height of the first and third bars
    third_bar_height = bar_data['Valeur'][bar_data['Type'] == 'Conso mesurée après\n$E_{f,après,corr}*f_{p}$'].values[0]
    # set the x-coordinate for the third bar
    x_coord_third_bar = 1.8  # this depends on the actual x-coordinate of the third bar
    # text for the arrow
    text_arrow_baisse_realisee = "Baisse\nmesurée\n"+str('{:.1f}'.format(bar_data['Valeur'][5])) + " MJ/m²"
    # add text at the midpoint of the arrow
    midpoint_height = (first_bar_height + third_bar_height) / 2
    # plot the line (arrow without arrowheads)
    ax.annotate("", xy=(x_coord_third_bar, third_bar_height), xytext=(x_coord_third_bar, first_bar_height),
                arrowprops=dict(arrowstyle="->", color='lightgreen', lw=4))  # increase lw for a thicker line
    # add the text over the line and centered
    u = ax.text(x_coord_third_bar, midpoint_height, text_arrow_baisse_realisee, ha='center', va='center', rotation=0,
            bbox=dict(boxstyle="round,pad=0.3", fc="lime", ec="lime", lw=2))

    #####################
    # titres
    # titre de l'histogramme
    title_text = str('{:.1f}'.format(bar_data['Valeur'][3]*100)) + "% de l'objectif atteint"
    title_color = 'darkgreen' if bar_data['Valeur'][3]*100 >= 85 else 'red'

    plt.title(title_text, weight='bold', color=title_color, loc='center', pad=15, fontsize=13, y=0.94)

    # sous-titre
    plt.suptitle(site, fontsize=16, x=0.515, y=0.97)
    # Modifier l'espacement entre sous-titre et titre
    plt.subplots_adjust (top=.905, bottom=.21, left=.06, right=.97, hspace=.2, wspace=.2)

    # date de génération du graphique
    now = datetime.now()
    date_str = str(now.strftime("%d-%m-%Y"))
    ax.text(1.0, -0.24, date_str, transform=ax.transAxes,
        ha='right', va='bottom', fontsize=8)

    # titre pour l'abscisse X
    plt.xlabel("\nBaisse d'IDC minimum pour obtenir la subvention = 85% * " +
               str('{:.1f}'.format(bar_data['Valeur'][4])) + " = " +
               str('{:.1f}'.format(bar_data['Valeur'][4]*0.85)) + ' MJ/m² \n$E_{f,après,corr}*f_{p}$ maximum pour obtenir la subvention ($(E_{f,après,corr}*f_{p})_{max→subv.}$) = ' +
               str('{:.1f}'.format(bar_data['Valeur'][0])) + " - " +
               str('{:.1f}'.format(bar_data['Valeur'][4]*0.85)) + " = " +
               str('{:.1f}'.format(bar_data['Valeur'][0] - bar_data['Valeur'][4]*0.85)) + " MJ/m²\nPourcentage de l'objectif atteint = " +
               str('{:.1f}'.format(bar_data['Valeur'][5])) + " / " + 
               str('{:.1f}'.format(bar_data['Valeur'][4]))+ " * 100 = " +
               str('{:.1f}'.format(bar_data['Valeur'][5]/bar_data['Valeur'][4]*100)) + "%", 
               loc='left', size=9)
    # titre pour l'ordonnée Y
    plt.ylabel("[MJ/m²/an]")


    # sauvegarder graphique
    plt.savefig (sauvegarde_png,dpi=600)
    del bar_data
    del bar_data1
    del bar_data2

    # nettoyage
    plt.close()

    return sauvegarde_png